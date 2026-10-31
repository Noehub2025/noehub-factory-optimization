#![cfg(unix)]
use serde_json::{Value, json};
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};
use workflow_harness::session::{ManagedCorrection, Session};
use workflow_harness::{Decision, QueuedWorkCorrection, Response, Role, Source, Task};

struct Fixture(PathBuf);
impl Fixture {
    fn new() -> Self {
        static NEXT: AtomicU64 = AtomicU64::new(0);
        let d = std::env::temp_dir().join(format!(
            "managed-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&d).unwrap();
        fs::write(d.join("source.md"), "Current governing source.\n").unwrap();
        let mut session = Session::create(
            Task {
                objective: "Retain old scope until its owner changes it".into(),
                controlling_objective: Some(0),
                workspace: d.clone(),
                constraints: "Only the assigned reversible fixture actions".into(),
                sources: vec![Source {
                    path: "source.md".into(),
                    first_line: 1,
                    last_line: 1,
                    purpose: "governing source".into(),
                    roles: vec![Role::Coordinator, Role::Worker],
                }],
                invocation_limit: 8,
                research: None,
            },
            &d.join("run"),
        )
        .unwrap();
        session.request().unwrap();
        Self(d)
    }
    fn worker(self) -> Self {
        let mut s = Session::open_managed(&self.run()).unwrap();
        s.accept(Response {
            invocation_id: 1,
            role: Role::Coordinator,
            decision: Decision::Work,
            summary: "Use the existing assignment".into(),
            assignment: "Old worker task".into(),
            actual_use: vec![],
            evidence: vec![],
            update: None,
        })
        .unwrap();
        s.request().unwrap();
        drop(s);
        self
    }
    fn run(&self) -> PathBuf {
        self.0.join("run")
    }
    fn state(&self) -> Value {
        serde_json::from_slice(&fs::read(self.run().join("state.json")).unwrap()).unwrap()
    }
    fn backend(&self, body: &str) -> Child {
        fs::write(self.0.join("backend.py"), format!("{PRELUDE}\n{body}\n")).unwrap();
        let mut child = Command::new(env!("CARGO_BIN_EXE_workflow-harness"))
            .args(["host", "managed-drive"])
            .arg(self.run())
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        writeln!(
            child.stdin.take().unwrap(),
            "{}",
            json!({"program":"/usr/bin/python3","args":[self.0.join("backend.py")]})
        )
        .unwrap();
        child
    }
    fn correct(&self) -> workflow_harness::Invocation {
        Session::open_managed(&self.run())
            .unwrap()
            .correct_managed_work(correction())
            .unwrap()
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}
fn correction() -> ManagedCorrection {
    ManagedCorrection {
        correction_id: "repair-1".into(),
        expected_invocation: 1,
        replacement: QueuedWorkCorrection {
            assignment: "Use the corrected scope and preserve completed evidence".into(),
            objective: Some("New objective scope".into()),
            constraints: Some("Current conditions remain explicit".into()),
            actual_use: None,
        },
    }
}
fn wait_file(path: &Path) {
    let deadline = Instant::now() + Duration::from_secs(10);
    while !path.exists() {
        assert!(Instant::now() < deadline, "missing {}", path.display());
        std::thread::sleep(Duration::from_millis(10));
    }
}
fn finish(mut child: Child) -> std::process::Output {
    let deadline = Instant::now() + Duration::from_secs(12);
    loop {
        if child.try_wait().unwrap().is_some() {
            let out = child.wait_with_output().unwrap();
            if !out.status.success() {
                eprintln!("host error: {}", String::from_utf8_lossy(&out.stderr));
            }
            return out;
        }
        if Instant::now() > deadline {
            let _ = child.kill();
            panic!("managed host failed to finish");
        }
        std::thread::sleep(Duration::from_millis(10));
    }
}
const PRELUDE: &str = r#"
import sys,json,pathlib,time
root=pathlib.Path.cwd()
request=json.loads(sys.stdin.readline())
ident=request['invocation_id']
def emit(obj): print(json.dumps(obj),flush=True)
def action(key,body,claimed=None):
    value={'kind':'action','action_id':key,'command':{'program':'/usr/bin/python3','args':['-c',body]}}
    if claimed is not None: value['invocation_id']=claimed
    emit(value)
def read(): return json.loads(sys.stdin.readline())
def done():
    evidence=root/('done-'+str(ident)+'.json')
    evidence.write_text(json.dumps({'invocation_id':ident,'protocol_completed':True}))
    emit({'kind':'return','response':{'invocation_id':ident,'role':request['role'],'decision':'observed' if request['role']=='worker' else 'finish','summary':'Retained fixture observations','evidence':[str(evidence)]}})
"#;

#[test]
fn actual_host_retires_noncooperative_worker_and_queued_actions() {
    let f = Fixture::new().worker();
    fs::write(f.0.join("produced.json"), r#"{"a":7,"b":16}"#).unwrap();
    fs::write(
        f.0.join("requests.json"),
        r#"[{"key":"b","factor":2,"offset":1},{"key":"a","factor":3,"offset":-1}]"#,
    )
    .unwrap();
    let child=f.backend(r#"
if ident==2:
    action('forge',"open('forged','w').write('bad')",3)
    assert read()['kind']=='denied'
    action('started',"from pathlib import Path; import time; Path('started').touch(); end=time.monotonic()+8\nwhile not Path('release').exists() and time.monotonic()<end: time.sleep(.01)\nPath('old-completed').touch()")
    action('queued',"open('forbidden','w').write('bad')")
    done()
    read()
    while True: action('stale',"open('forbidden','w').write('bad')",3); time.sleep(.02)
else:
    assert 'New objective scope' in request['prompt']
    assert 'Current conditions remain explicit' in request['prompt']
    assert 'Corrected governing source.' in request['prompt']
    assert 'Use the produced representation for current requests' in request['prompt']
    (root/'installed.json').write_text(json.dumps(request))
    action('current',"import json; p=json.load(open('produced.json')); requests=json.load(open('requests.json')); out=[p[r['key']]*r['factor']+r['offset'] for r in requests]; json.dump(out,open('consumer-result.json','w')); open('current-effect','w').write('good')")
    assert read()['kind']=='action_result'
    done()
"#);
    wait_file(&f.0.join("started"));
    fs::write(f.0.join("source.md"), "Corrected governing source.\n").unwrap();
    assert!(
        Session::open_managed(&f.run())
            .unwrap()
            .prepare_host_dispatch(2, "legacy-old".into())
            .unwrap_err()
            .contains("managed host")
    );
    let mut fix = correction();
    fix.expected_invocation = 2;
    fix.replacement.assignment =
        "Use the produced representation for current requests; preserve completed evidence".into();
    let next = Session::open_managed(&f.run())
        .unwrap()
        .correct_managed_work(fix.clone())
        .unwrap();
    assert_eq!(next.invocation_id, 3);
    assert!(
        Session::open_managed(&f.run())
            .unwrap()
            .prepare_host_dispatch(3, "legacy-new".into())
            .unwrap_err()
            .contains("managed host")
    );
    assert_eq!(
        Session::open_managed(&f.run())
            .unwrap()
            .correct_managed_work(fix)
            .unwrap()
            .invocation_id,
        3,
        "retry recovers the same publication"
    );
    assert_eq!(f.state()["managed"]["invocations"]["2"]["phase"], "retired");
    // An unrelated Session remains usable while this one's old effect settles.
    let other = Fixture::new();
    assert!(finish(other.backend("done()")).status.success());
    fs::write(f.0.join("release"), "").unwrap();
    let output = finish(child);
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(f.0.join("old-completed").exists());
    assert!(f.0.join("current-effect").exists());
    let consumed: Value =
        serde_json::from_slice(&fs::read(f.0.join("consumer-result.json")).unwrap()).unwrap();
    assert_eq!(consumed, json!([33, 20]));
    assert!(!f.0.join("forbidden").exists());
    assert!(!f.0.join("forged").exists());
    let old_messages = fs::read_to_string(f.run().join("managed-2.jsonl")).unwrap();
    assert!(old_messages.contains("queued"));
    assert!(old_messages.contains("\"kind\": \"return\""));
    assert!(!f.run().join("response-2.json").exists());
    assert_eq!(
        f.state()["managed"]["invocations"]["2"]["actions"]["started"]["outcome"],
        0
    );
    assert_eq!(
        f.state()["managed"]["invocations"]["3"]["phase"],
        "completed"
    );
}

#[test]
fn correction_does_not_require_old_backend_acknowledgement() {
    let f = Fixture::new();
    let child = f.backend(r#"
if ident==1:
    action('started',"from pathlib import Path; import time; Path('started').touch(); end=time.monotonic()+8\nwhile not Path('release').exists() and time.monotonic()<end: time.sleep(.01)\nPath('old-completed').touch()")
    sys.exit(0)
else:
    action('current',"open('current-effect','w').write('good')")
    assert read()['kind']=='action_result'
    done()
"#);
    wait_file(&f.0.join("started"));
    f.correct();
    fs::write(f.0.join("release"), "").unwrap();
    assert!(finish(child).status.success());
    assert!(f.0.join("old-completed").exists());
    assert!(f.0.join("current-effect").exists());
}

#[test]
fn selected_usage_return_condition_still_controls_managed_actions() {
    let f = Fixture::new().worker();
    let mut state = f.state();
    state["runtime"]["segment"] = json!({"observation":"bounded observation", "return_when":"selected model usage reached", "elapsed_ms":null, "model_tokens":5, "return_on_change":[]});
    fs::write(
        f.run().join("state.json"),
        serde_json::to_vec(&state).unwrap(),
    )
    .unwrap();
    let child = f.backend(
        r#"
emit({'kind':'event','event':{'kind':'usage','total':{'model_tokens':5}}})
assert read()['kind']=='recorded'
action('after-limit',"open('forbidden','w').write('bad')")
assert read()['kind']=='denied'
done()
"#,
    );
    assert!(finish(child).status.success());
    assert!(!f.0.join("forbidden").exists());
    assert_eq!(
        f.state()["runtime"]["executions"][0]["usage"]["model_tokens"],
        5
    );
    assert_eq!(
        f.state()["runtime"]["executions"][0]["effects_settled"],
        true
    );
}

#[test]
fn stale_live_source_and_duplicate_action_cannot_dispatch() {
    let f = Fixture::new();
    let child = f.backend(
        r#"
action('once',"open('once','a').write('x')")
assert read()['kind']=='action_result'
action('once',"open('once','a').write('x')")
assert read()['kind']=='denied'
action('edit',"open('source.md','w').write('Changed governing source.\\n')")
assert read()['kind']=='action_result'
action('after',"open('forbidden','w').write('bad')")
assert read()['kind']=='denied'
(root/'checked').touch()
done()
"#,
    );
    let output = finish(child);
    assert!(
        !output.status.success(),
        "a stale current return must not be adopted"
    );
    assert!(f.0.join("checked").exists());
    assert_eq!(fs::read_to_string(f.0.join("once")).unwrap(), "x");
    assert!(!f.0.join("forbidden").exists());
    assert!(f.run().join("managed-return-1.json").exists());
}

#[test]
fn lost_installation_or_effect_receipt_never_replays() {
    let f = Fixture::new();
    let child = f.backend("(root/'installed').touch(); time.sleep(1); done()");
    wait_file(&f.0.join("installed"));
    let duplicate = finish(f.backend("done()"));
    assert!(!duplicate.status.success());
    let first = finish(child);
    assert!(first.status.success());
    // Reconstruct a crash after effect intent but before any host outcome.
    let g = Fixture::new();
    let mut state = g.state();
    state["managed"]["invocations"]["1"] = json!({"phase":"installing","actions":{"lost":{"command":{"program":"/bin/sh","args":[]},"outcome":null,"not_started":false,"stdout":g.0.join("out"),"stderr":g.0.join("err")}}});
    fs::write(
        g.run().join("state.json"),
        serde_json::to_vec(&state).unwrap(),
    )
    .unwrap();
    g.correct();
    let output = finish(g.backend("(root/'replayed').touch(); done()"));
    assert!(!output.status.success());
    assert!(!g.0.join("replayed").exists());
    // A correlated persisted receipt can settle the old effect without replay.
    fs::write(g.run().join("action-1-lost.receipt.json"),serde_json::to_vec(&json!({"invocation_id":1,"action_id":"lost","command":{"program":"/bin/sh","args":[]},"exit_code":0})).unwrap()).unwrap();
    assert!(finish(g.backend("done()")).status.success());
    assert_eq!(
        g.state()["managed"]["invocations"]["1"]["actions"]["lost"]["outcome"],
        0
    );
}

#[test]
fn unsuccessful_correction_keeps_original_state_and_key_scope() {
    let f = Fixture::new();
    let initial = f.state();
    let invalid = workflow_harness::session::ProcessAdapter {
        program: "missing-relative-backend".into(),
        args: vec![],
    };
    assert!(
        workflow_harness::session::drive_managed(&f.run(), &invalid)
            .unwrap_err()
            .contains("absolute executable")
    );
    assert_eq!(
        f.state(),
        initial,
        "preflight refusal must not create an uncertain installation"
    );
    let child = f.backend("(root/'installed').touch(); time.sleep(1); done()");
    wait_file(&f.0.join("installed"));
    let mut s = Session::open_managed(&f.run()).unwrap();
    let mut bad = correction();
    bad.expected_invocation = 900;
    assert!(s.correct_managed_work(bad).is_err());
    assert_eq!(s.runtime.outstanding().unwrap().invocation_id, 1);
    let next = s.correct_managed_work(correction()).unwrap();
    let mut reused = correction();
    reused.replacement.assignment = "different".into();
    assert!(s.correct_managed_work(reused).is_err());
    assert_eq!(next.invocation_id, 2);
    drop(s);
    assert!(finish(child).status.success());
}

#[test]
fn paused_correction_keeps_complete_successor_and_previously_admitted_effect() {
    let f = Fixture::new().worker();
    let child = f.backend(
        r#"
action('started',"from pathlib import Path; import time; Path('started').touch(); end=time.monotonic()+8\nwhile not Path('release').exists() and time.monotonic()<end: time.sleep(.01)\nPath('effect-completed').write_text('once')")
read()
"#,
    );
    wait_file(&f.0.join("started"));
    Session::request_pause(&f.run(), "Owner paused new work".into()).unwrap();
    let mut change = correction();
    change.expected_invocation = 2;
    let mut session = Session::open_managed(&f.run()).unwrap();
    let successor = session.correct_managed_work(change.clone()).unwrap();
    drop(session);
    let paused = f.state();
    assert_eq!(paused["runtime"]["paused"], "Owner paused new work");
    assert_eq!(paused["managed"]["invocations"]["2"]["phase"], "retired");
    assert_eq!(
        paused["runtime"]["outstanding"]["invocation_id"],
        successor.invocation_id
    );
    assert!(
        f.run()
            .join(format!("request-{}.json", successor.invocation_id))
            .is_file()
    );
    assert!(paused["managed"]["invocations"]["2"]["actions"]["started"]["outcome"].is_null());
    fs::write(f.0.join("release"), "continue the already admitted effect").unwrap();
    let held = finish(child);
    assert!(!held.status.success());
    assert!(String::from_utf8_lossy(&held.stderr).contains("run is paused"));
    wait_file(&f.0.join("effect-completed"));
    let mut resumed = Session::open_managed(&f.run()).unwrap();
    resumed.unpause().unwrap();
    let recovered = resumed.correct_managed_work(change).unwrap();
    assert_eq!(recovered.invocation_id, successor.invocation_id);
    drop(resumed);
    assert!(f.state()["runtime"]["paused"].is_null());
    assert_eq!(
        fs::read_to_string(f.0.join("effect-completed")).unwrap(),
        "once"
    );
}
