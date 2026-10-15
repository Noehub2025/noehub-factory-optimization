"""Current saved-owner applicability without a mandatory branch movement."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import frontier_references as refs


class CurrentBasisTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.git('init')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        self.task = self.root / 'TASK.md'
        self.task.write_text('---\nfeedback_not_due: Current prerequisite incomplete.\n---\n# Task\nOriginal work.\n')
        (self.root / 'evidence.json').write_text('{"result":3}')
        self.git('add', '.')
        self.git('commit', '-m', 'Old state')
        old = self.git('rev-parse', 'HEAD')
        self.task.write_text(self.task.read_text().replace('Original work.', 'Adopted completed-epoch evidence.'))
        self.git('add', 'TASK.md')
        self.git('commit', '-m', 'Saved current owner')
        self.saved = self.git('rev-parse', 'HEAD')
        self.git('update-ref', 'HEAD', old)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.PIPE, text=True).strip()

    def prepare(self):
        return refs.prepare_resolver(self.root, self.saved, 'evidence.json', owner_source='TASK.md')

    def test_saved_current_owner_does_not_require_head_movement(self):
        prepared = self.prepare()
        result = refs.bind_resolution(self.root, prepared, {'row':13, 'reason':'Continue this valid current work.'})
        self.assertEqual(result['objective_owner']['commit'], self.saved)
        self.assertNotEqual(self.git('rev-parse', 'HEAD'), self.saved)

    def test_unsaved_selected_source_change_is_rejected(self):
        prepared = self.prepare()
        self.task.write_text(self.task.read_text().replace('completed-epoch', 'a different'))
        with self.assertRaisesRegex(refs.ReferenceError, 'basis changed'):
            refs.bind_resolution(self.root, prepared, {'row':13})

    def test_unsaved_owner_timing_change_is_rejected(self):
        self.task.write_text(self.task.read_text().replace('prerequisite incomplete', 'optional work complete'))
        with self.assertRaisesRegex(refs.ReferenceError, 'basis changed'):
            self.prepare()


if __name__ == '__main__':
    unittest.main()
