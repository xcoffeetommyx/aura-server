import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import owner_ip_refresh
import ip_deploy


class OwnerIPRefreshTests(unittest.TestCase):
    def test_requires_explicit_opt_in(self):
        value = dict(version=1, publicIP="8.8.8.8", certName="aura-home-ip")
        self.assertNotIn("ownerEnabled", ip_deploy.configuration(value))
        for invalid in (1, "true", None):
            with self.assertRaises(ValueError): ip_deploy.configuration(dict(value, ownerEnabled=invalid))

    def test_wrong_owner_host_cannot_rewrite_certificate_or_start_service(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); config = root / "config.json"
            config.write_text(json.dumps(dict(ownerHost="old.example:9443"))); config.chmod(0o600)
            with patch.object(owner_ip_refresh.renew, "owner_install") as install:
                with self.assertRaises(ValueError):
                    owner_ip_refresh.refresh(root, root / "cert", root / "key", "8.8.8.8", os.getuid(), os.getgid(), True)
                install.assert_not_called()

    def test_valid_host_preserves_stopped_disposition_and_uses_ip_verification(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); config = root / "config.json"
            config.write_text(json.dumps(dict(ownerHost="8.8.8.8:9443"))); config.chmod(0o600)
            with patch.object(owner_ip_refresh.renew, "validate_pair") as verify, patch.object(owner_ip_refresh.renew, "owner_install") as install:
                owner_ip_refresh.refresh(root, root / "cert", root / "key", "8.8.8.8", os.getuid(), os.getgid(), False)
                self.assertTrue(verify.call_args.kwargs["ip_identifier"])
                self.assertFalse(install.call_args.args[5])
