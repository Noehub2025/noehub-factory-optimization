use serde_json::json;
use std::{
    fs,
    path::PathBuf,
    sync::atomic::{AtomicUsize, Ordering},
};
use workflow_harness::session::{ProcessAdapter, Session};
use workflow_harness::{Response, Task};

static NEXT: AtomicUsize = AtomicUsize::new(0);
struct Fixture(PathBuf);
impl Fixture {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "context-delivery-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir_all(&root).unwrap();
        fs::write(
            root.join("goal.md"),
            "Whole objective.\nQualification outside selected excerpt.\n",
        )
        .unwrap();
        Self(root)
    }
    fn session(&self) -> Session {
        let task: Task = serde_json::from_value(json!({
            "objective":"Local question", "controlling_objective":0, "workspace":self.0,
            "constraints":"No external effects", "invocation_limit":20,
            "sources":[{"path":"goal.md","first_line":1,"last_line":1,"purpose":"Goal", "roles":["coordinator","resolver","worker"]}]
        })).unwrap();
        Session::create(task, &self.0.join("run")).unwrap()
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

#[test]
fn final_input_has_one_goal_and_independently_readable_exact_evidence() {
    let f = Fixture::new();
    let mut session = f.session();
    let request = session.request().unwrap();
    assert_eq!(
        request
            .prompt
            .matches("Qualification outside selected excerpt.")
            .count(),
        1
    );
    let source = session
        .runtime
        .read_context_evidence("/full_sources/0")
        .unwrap();
    assert!(source.as_str().unwrap().contains("Qualification"));
    session.verify_queued_context(&request).unwrap();
    assert!(session.verify_queued_current_use(&request).is_err());
    // Repeated delivery does not append another evidence or policy block.
    assert!(session.request().is_err());
    assert_eq!(
        session.runtime.outstanding().unwrap().prompt,
        request.prompt
    );
}

#[test]
fn all_roles_detect_source_and_retained_evidence_changes_before_dispatch() {
    let f = Fixture::new();
    let mut session = f.session();
    let request = session.request().unwrap();
    fs::write(f.0.join("irrelevant.md"), "Unrelated history").unwrap();
    session.verify_queued_context(&request).unwrap();
    fs::write(
        f.0.join("goal.md"),
        "Whole objective.\nChanged governing condition.\n",
    )
    .unwrap();
    assert!(
        session
            .verify_queued_context(&request)
            .unwrap_err()
            .contains("source changed")
    );
    fs::write(
        f.0.join("goal.md"),
        "Whole objective.\nQualification outside selected excerpt.\n",
    )
    .unwrap();
    let locator: serde_json::Value =
        serde_json::from_slice(&fs::read(f.0.join("run/request-1-evidence.json")).unwrap())
            .unwrap();
    fs::write(locator["path"].as_str().unwrap(), "{}").unwrap();
    assert!(
        session
            .verify_queued_context(&request)
            .unwrap_err()
            .contains("evidence changed")
    );
    assert!(
        session
            .runtime
            .read_context_evidence("/full_sources/0")
            .is_err()
    );
}

#[test]
fn tampered_saved_process_request_is_rejected_before_creating_effect_files() {
    let f = Fixture::new();
    let mut session = f.session();
    let mut request = session.request().unwrap();
    request.prompt = "Different task".into();
    fs::write(
        f.0.join("run/request-1.json"),
        serde_json::to_vec(&request).unwrap(),
    )
    .unwrap();
    let error = session
        .invoke(&ProcessAdapter {
            program: f.0.join("goal.md"),
            args: vec![],
        })
        .unwrap_err();
    assert!(error.contains("different queued request"), "{error}");
    assert!(!f.0.join("run/stdout-1.json").exists());
}

#[test]
fn only_explicit_owner_incorporation_removes_returns_and_survives_cold_open() {
    let f = Fixture::new();
    let mut session = f.session();
    session.request().unwrap();
    let first: Response = serde_json::from_value(
        json!({"invocation_id":1,"role":"coordinator","decision":"work",
        "summary":"OLD_PROCESS_HISTORY".repeat(1000),"assignment":"Obtain one observation",
        "update":{"remaining_work":[],"interpretation":"Initial understanding", "segment":null,
        "context":{"understanding":"C remains necessary. Z remains open.","incorporates":[1]}}}),
    )
    .unwrap();
    session.accept(first).unwrap();
    let worker = session.request().unwrap();
    assert!(!worker.prompt.contains("OLD_PROCESS_HISTORY"));
    assert!(worker.prompt.contains("Z remains open"));
    session
        .accept(
            serde_json::from_value(
                json!({"invocation_id":2,"role":"worker","decision":"observed",
        "summary":"New contradiction: C fails in setting D.","evidence":[f.0.join("goal.md")]}),
            )
            .unwrap(),
        )
        .unwrap();
    let coordinator = session.request().unwrap();
    assert!(coordinator.prompt.contains("New contradiction"));
    session.accept(serde_json::from_value(json!({"invocation_id":3,"role":"coordinator","decision":"work",
        "summary":"Adopt the observation; narrow C, keep Z open.","assignment":"Discriminate the explanation",
        "update":{"remaining_work":[],"interpretation":"C is conditional on not D.","segment":null,
        "context":{"understanding":"C is supported outside D only; Z remains open.","incorporates":[1,2,3]}}})).unwrap()).unwrap();
    drop(session);
    let mut recovered = Session::open(&f.0.join("run")).unwrap();
    let input = recovered.request().unwrap();
    assert!(input.prompt.contains("outside D only"));
    assert!(!input.prompt.contains("New contradiction:"));
    let retained = recovered
        .runtime
        .read_context_evidence("/returns/1/summary")
        .unwrap();
    assert!(retained.as_str().unwrap().contains("New contradiction"));
}

#[test]
fn unchanged_returns_advance_coverage_without_rewriting_the_account_or_copying_history() {
    let f = Fixture::new();
    let mut session = f.session();
    session.request().unwrap();
    session
        .accept(
            serde_json::from_value(
                json!({"invocation_id":1,"role":"coordinator","decision":"work",
        "summary":"Old detailed account".repeat(1000),"assignment":"Observe",
        "update":{"remaining_work":[],"interpretation":"C only", "segment":null,
        "context":{"understanding":"C only; Z remains open.","incorporates":[1]}}}),
            )
            .unwrap(),
        )
        .unwrap();
    session.request().unwrap();
    session
        .accept(
            serde_json::from_value(
                json!({"invocation_id":2,"role":"worker","decision":"observed",
        "summary":"No change from this observation","evidence":[f.0.join("goal.md")]}),
            )
            .unwrap(),
        )
        .unwrap();
    session.request().unwrap();
    session
        .accept(
            serde_json::from_value(
                json!({"invocation_id":3,"role":"coordinator","decision":"work",
        "summary":"No change to adopted understanding", "assignment":"Next observation",
        "update":{"remaining_work":[],"interpretation":"Same conditions", "segment":null,
        "context_unchanged":[2,3]}}),
            )
            .unwrap(),
        )
        .unwrap();
    let request = session.request().unwrap();
    assert!(request.prompt.contains("C only; Z remains open."));
    assert!(!request.prompt.contains("No change from this observation"));
    let large_objects = fs::read_dir(f.0.join("run/context-sources"))
        .unwrap()
        .filter(|entry| entry.as_ref().unwrap().metadata().unwrap().len() > 10_000)
        .count();
    assert_eq!(
        large_objects, 1,
        "the original return is stored once across request manifests"
    );
    let locator: serde_json::Value =
        serde_json::from_slice(&fs::read(f.0.join("run/request-4-evidence.json")).unwrap())
            .unwrap();
    // Read through the public path while the writer lock is still held.
    let first = Session::read_saved_context(
        &f.0.join("run"),
        locator["sha256"].as_str().unwrap(),
        "/returns/0/summary",
    )
    .unwrap();
    assert!(first.as_str().unwrap().starts_with("Old detailed account"));
}

#[test]
fn quoted_delivery_marker_cannot_suppress_actual_binding() {
    let f = Fixture::new();
    fs::write(
        f.0.join("goal.md"),
        "A quotation follows.\nExact retained context and validation evidence: old-example.json\n",
    )
    .unwrap();
    let mut session = f.session();
    let request = session.request().unwrap();
    assert!(f.0.join("run/request-1-evidence.json").is_file());
    session.verify_queued_context(&request).unwrap();
    assert!(
        session
            .runtime
            .read_context_evidence("/full_sources/0")
            .unwrap()
            .as_str()
            .unwrap()
            .contains("old-example")
    );
}

#[test]
fn interrupted_temp_is_not_a_published_version_and_return_ids_can_have_gaps() {
    use workflow_harness::context::Snapshot;
    let f = Fixture::new();
    let directory = f.0.join("objects");
    fs::create_dir(&directory).unwrap();
    fs::write(directory.join(".interrupted-write.tmp"), "partial").unwrap();
    let first = Snapshot::retain(&directory, &json!({"invocation_id":1,"summary":"One"})).unwrap();
    let third =
        Snapshot::retain(&directory, &json!({"invocation_id":3,"summary":"Three"})).unwrap();
    let manifest = Snapshot::retain(
        &directory,
        &json!({"returns":[first,third],"return_ids":{"1":0,"3":1}}),
    )
    .unwrap();
    assert_eq!(
        manifest.expand("/by_invocation/3/summary").unwrap(),
        "Three"
    );
    assert!(manifest.expand("/by_invocation/2").is_err());
    fs::write(&manifest.path, "damaged published object").unwrap();
    assert!(manifest.read().is_err());
}
