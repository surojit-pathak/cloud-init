from unittest import TestCase
from mocker import MockerTestCase
from tempfile import mkdtemp
from shutil import rmtree
import os
import stat

from cloudinit.util import mergedict, get_cfg_option_list_or_str, write_file

class TestMergeDict(TestCase):
    def test_simple_merge(self):
        source = {"key1": "value1"}
        candidate = {"key2": "value2"}
        result = mergedict(source, candidate)
        self.assertEqual({"key1": "value1", "key2": "value2"}, result)

    def test_nested_merge(self):
        source = {"key1": {"key1.1": "value1.1"}}
        candidate = {"key1": {"key1.2": "value1.2"}}
        result = mergedict(source, candidate)
        self.assertEqual(
            {"key1": {"key1.1": "value1.1", "key1.2": "value1.2"}}, result)

    def test_merge_does_not_override(self):
        source = {"key1": "value1", "key2": "value2"}
        candidate = {"key2": "value2", "key2": "NEW VALUE"}
        result = mergedict(source, candidate)
        self.assertEqual(source, result)

    def test_empty_candidate(self):
        source = {"key": "value"}
        candidate = {}
        result = mergedict(source, candidate)
        self.assertEqual(source, result)

    def test_empty_source(self):
        source = {}
        candidate = {"key": "value"}
        result = mergedict(source, candidate)
        self.assertEqual(candidate, result)

    def test_non_dict_candidate(self):
        source = {"key": "value"}
        candidate = "not a dict"
        result = mergedict(source, candidate)
        self.assertEqual(source, result)

    def test_non_dict_source(self):
        source = "not a dict"
        candidate = {"key": "value"}
        result = mergedict(source, candidate)
        self.assertEqual(source, result)

    def test_neither_dict(self):
        source = "source"
        candidate = "candidate"
        result = mergedict(source, candidate)
        self.assertEqual(source, result)

class TestGetCfgOptionListOrStr(TestCase):
    def test_not_found_no_default(self):
        config = {}
        result = get_cfg_option_list_or_str(config, "key")
        self.assertIsNone(result)

    def test_not_found_with_default(self):
        config = {}
        result = get_cfg_option_list_or_str(config, "key", default=["DEFAULT"])
        self.assertEqual(["DEFAULT"], result)

    def test_found_with_default(self):
        config = {"key": ["value1"]}
        result = get_cfg_option_list_or_str(config, "key", default=["DEFAULT"])
        self.assertEqual(["value1"], result)

    def test_found_convert_to_list(self):
        config = {"key": "value1"}
        result = get_cfg_option_list_or_str(config, "key")
        self.assertEqual(["value1"], result)

    def test_value_is_none(self):
        config = {"key": None}
        result = get_cfg_option_list_or_str(config, "key")
        self.assertEqual([], result)

class TestWriteFile(MockerTestCase):
    def setUp(self):
        super(TestWriteFile, self).setUp()
        # Make a temp directoy for tests to use.
        self.tmp = mkdtemp(prefix="unittest_")

    def tearDown(self):
        super(TestWriteFile, self).tearDown()
        # Clean up temp directory
        rmtree(self.tmp)

    def test_basic_usage(self):
        """Verify basic usage with default args."""
        path = os.path.join(self.tmp, "NewFile.txt")
        contents = "Hey there"

        write_file(path, contents)

        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            create_contents = f.read()
            self.assertEqual(contents, create_contents)
        file_stat = os.stat(path)
        self.assertEqual(0644, stat.S_IMODE(file_stat.st_mode))

    def test_dir_is_created_if_required(self):
        """Verifiy that directories are created is required."""
        dirname = os.path.join(self.tmp, "subdir")
        path = os.path.join(dirname, "NewFile.txt")
        contents = "Hey there"

        write_file(path, contents)

        self.assertTrue(os.path.isdir(dirname))
        self.assertTrue(os.path.isfile(path))

    def test_custom_mode(self):
        """Verify custom mode works properly."""
        path = os.path.join(self.tmp, "NewFile.txt")
        contents = "Hey there"

        write_file(path, contents, mode=0666)

        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.isfile(path))
        file_stat = os.stat(path)
        self.assertEqual(0666, stat.S_IMODE(file_stat.st_mode))

    def test_custom_omode(self):
        """Verify custom omode works properly."""
        path = os.path.join(self.tmp, "NewFile.txt")
        contents = "Hey there"

        # Create file first with basic content
        with open(path, "wb") as f:
            f.write("LINE1\n")
        write_file(path, contents, omode="a")

        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            create_contents = f.read()
            self.assertEqual("LINE1\nHey there", create_contents)

    def test_restorecon_if_possible_is_called(self):
        """Make sure the restorecon_if_possible is called correctly."""
        path = os.path.join(self.tmp, "NewFile.txt")
        contents = "Hey there"

        # Mock out the restorecon_if_possible call to test if it's called.
        mock_restorecon = self.mocker.replace(
            "cloudinit.util.restorecon_if_possible", passthrough=False)
        mock_restorecon(path)
        self.mocker.replay()

        write_file(path, contents)
