# Copyright 2023-2024. WebPros International GmbH. All rights reserved.
import json
import os
from unittest import mock

from src import action
from tests.testcase import TestCase


class SimpleAction(action.ActiveAction):
    def __init__(self, name="Simple action"):
        self.name = name
        self.description = "Simple action description"

    def _prepare_action(self) -> action.ActionResult:
        return action.ActionResult()

    def _post_action(self) -> action.ActionResult:
        return action.ActionResult()

    def _revert_action(self) -> action.ActionResult:
        return action.ActionResult()


class SkipAction(action.ActiveAction):
    def __init__(self):
        self.name = "Skip action"
        self.description = "Skip action description"

    def _is_required(self):
        return False

    def _prepare_action(self) -> action.ActionResult:
        return action.ActionResult()

    def _post_action(self) -> action.ActionResult:
        return action.ActionResult()

    def _revert_action(self) -> action.ActionResult:
        return action.ActionResult()


class PrepareActionsFlowForTests(action.PrepareActionsFlow):
    def __init__(self, stages):
        super().__init__(stages, ".", flow_tracker=None)


class SavedAction(action.ActiveAction):
    def __init__(self):
        self.name = "saved"
        self.description = "Saved action description"

    def _prepare_action(self) -> action.ActionResult:
        return action.ActionResult()

    def _post_action(self) -> action.ActionResult:
        return action.ActionResult()

    def _revert_action(self) -> action.ActionResult:
        return action.ActionResult()


def check_saved_state(phase, stage, saved_action_state, should_be_called):
    simple_action = SimpleAction()
    saved_action = SavedAction()

    if phase not in ["prepare", "finish", "revert"]:
        raise ValueError("Unknown phase")

    function_name = "_prepare_action" if phase == "prepare" else "_post_action" if phase == "finish" else "_revert_action"
    setattr(simple_action, function_name, mock.Mock(return_value=action.ActionResult()))
    setattr(saved_action, function_name, mock.Mock(return_value=action.ActionResult()))

    simple_action_target_mock = getattr(simple_action, function_name)
    saved_action_target_mock = getattr(saved_action, function_name)

    with open("actions.json", "w") as actions_data_file:
        state_json = json.dumps({"actions": [{"stage": stage, "name": "saved", "state": saved_action_state}]})
        actions_data_file.write(state_json)

    actionFlowClass = PrepareActionsFlowForTests if phase == "prepare" else FinishActionsFlowForTests if phase == "finish" else RevertActionsFlowForTests
    with actionFlowClass({stage: [simple_action, saved_action]}) as flow:
        flow.validate_actions()
        flow.pass_actions()

    simple_action_target_mock.assert_called_once()
    if should_be_called:
        saved_action_target_mock.assert_called_once()
    else:
        saved_action_target_mock.assert_not_called()


class TestPrepareActionsFlow(TestCase):

    def setUp(self):
        with open("actions.json", "w") as actions_data_file:
            actions_data_file.write('{ "actions": [] }')

    def tearDown(self):
        os.remove("actions.json")

    def test_one_simple_action(self):
        simple_action = SimpleAction()
        simple_action._prepare_action = mock.Mock(return_value=action.ActionResult())
        with PrepareActionsFlowForTests({"test_one_simple_action": [simple_action]}) as flow:
            flow.validate_actions()
            flow.pass_actions()

        simple_action._prepare_action.assert_called_once()

    def test_several_simple_actions(self):
        actions = []
        for i in range(5):
            simple_action = SimpleAction(f"Simple action {i}")
            simple_action._prepare_action = mock.Mock(return_value=action.ActionResult())
            actions.append(simple_action)

        with PrepareActionsFlowForTests({"test_several_simple_actions": actions}) as flow:
            flow.validate_actions()
            flow.pass_actions()

        for act in actions:
            act._prepare_action.assert_called_once()

    def test_several_steps(self):
        simple_action_step_1 = SimpleAction()
        simple_action_step_1._prepare_action = mock.Mock(return_value=action.ActionResult())
        simple_action_step_2 = SimpleAction()
        simple_action_step_2._prepare_action = mock.Mock(return_value=action.ActionResult())

        with PrepareActionsFlowForTests({"test_several_steps 1": [simple_action_step_1], "test_several_steps 2": [simple_action_step_2]}) as flow:
            flow.validate_actions()
            flow.pass_actions()

        simple_action_step_1._prepare_action.assert_called_once()
        simple_action_step_2._prepare_action.assert_called_once()

    def test_skip_action(self):
        simple_action = SimpleAction()
        simple_action._prepare_action = mock.Mock(return_value=action.ActionResult())
        skip_action = SkipAction()
        skip_action._prepare_action = mock.Mock(return_value=action.ActionResult())

        with PrepareActionsFlowForTests({"test_skip_action": [simple_action, skip_action]}) as flow:
            flow.validate_actions()
            flow.pass_actions()

        simple_action._prepare_action.assert_called_once()
        skip_action._prepare_action.assert_not_called()

    def test_preparation_skip_based_on_saved_success_state(self):
        check_saved_state("prepare", "test_skip_based_on_saved_success_state", "success", False)

    def test_preparation_pass_based_on_saved_skip_state(self):
        check_saved_state("prepare", "test_skip_based_on_saved_success_state", "skip", True)

    def test_preparation_pass_based_on_saved_failed_state(self):
        check_saved_state("prepare", "test_skip_based_on_saved_success_state", "failed", True)


class FinishActionsFlowForTests(action.FinishActionsFlow):
    def __init__(self, stages):
        super().__init__(stages, ".", flow_tracker=None)


class TestFinishActionsFlow(TestCase):

    def setUp(self):
        with open("actions.json", "w") as actions_data_file:
            actions_data_file.write('{ "actions": [] }')

    def tearDown(self):
        # Flow removes the file by itself
        pass

    def test_one_simple_action(self):
        simple_action = SimpleAction()
        simple_action._post_action = mock.Mock(return_value=action.ActionResult())
        with FinishActionsFlowForTests({"test_one_simple_action": [simple_action]}) as flow:
            flow.validate_actions()
            flow.pass_actions()

        simple_action._post_action.assert_called_once()

    def test_several_simple_actions(self):
        actions = []
        for _ in range(5):
            simple_action = SimpleAction()
            simple_action._post_action = mock.Mock(return_value=action.ActionResult())
            actions.append(simple_action)

        with FinishActionsFlowForTests({"test_several_simple_actions": actions}) as flow:
            flow.validate_actions()
            flow.pass_actions()

        for act in actions:
            act._post_action.assert_called_once()

    def test_several_steps(self):
        simple_action_step_1 = SimpleAction()
        simple_action_step_1._post_action = mock.Mock(return_value=action.ActionResult())
        simple_action_step_2 = SimpleAction()
        simple_action_step_2._post_action = mock.Mock(return_value=action.ActionResult())

        with FinishActionsFlowForTests({"test_several_steps 1": [simple_action_step_1], "test_several_steps 2": [simple_action_step_2]}) as flow:
            flow.validate_actions()
            flow.pass_actions()

        simple_action_step_1._post_action.assert_called_once()
        simple_action_step_2._post_action.assert_called_once()

    def test_skip_action(self):
        simple_action = SimpleAction()
        simple_action._post_action = mock.Mock(return_value=action.ActionResult())
        skip_action = SkipAction()
        skip_action._post_action = mock.Mock(return_value=action.ActionResult())

        with FinishActionsFlowForTests({"test_skip_action": [simple_action, skip_action]}) as flow:
            flow.validate_actions()
            flow.pass_actions()

        simple_action._post_action.assert_called_once()
        skip_action._post_action.assert_not_called()

    def test_finish_pass_based_on_success_saved_state(self):
        check_saved_state("finish", "test_finish_pass_based_on_success_saved_state", "success", True)

    def test_finish_skip_based_on_skip_saved_state(self):
        check_saved_state("finish", "test_finish_skip_based_on_skip_saved_state", "skip", False)

    def test_finish_skip_based_on_failed_saved_state(self):
        check_saved_state("finish", "test_finish_skip_based_on_failed_saved_state", "failed", False)


class RevertActionsFlowForTests(action.RevertActionsFlow):
    def __init__(self, stages):
        super().__init__(stages, ".", flow_tracker=None)


class TestRevertActionsFlow(TestCase):

    def setUp(self):
        with open("actions.json", "w") as actions_data_file:
            actions_data_file.write('{ "actions": [] }')

    def tearDown(self):
        # Flow removes the file by itself
        pass

    def test_one_simple_action(self):
        simple_action = SimpleAction()
        simple_action._revert_action = mock.Mock(return_value=action.ActionResult())
        with RevertActionsFlowForTests({"test_one_simple_action": [simple_action]}) as flow:
            flow.validate_actions()
            flow.pass_actions()

        simple_action._revert_action.assert_called_once()

    def test_several_simple_actions(self):
        actions = []
        for _ in range(5):
            simple_action = SimpleAction()
            simple_action._revert_action = mock.Mock(return_value=action.ActionResult())
            actions.append(simple_action)

        with RevertActionsFlowForTests({"test_several_simple_actions": actions}) as flow:
            flow.validate_actions()
            flow.pass_actions()

        for act in actions:
            act._revert_action.assert_called_once()

    def test_several_steps(self):
        simple_action_step_1 = SimpleAction()
        simple_action_step_1._revert_action = mock.Mock(return_value=action.ActionResult())
        simple_action_step_2 = SimpleAction()
        simple_action_step_2._revert_action = mock.Mock(return_value=action.ActionResult())

        with RevertActionsFlowForTests({"test_several_steps 1": [simple_action_step_1], "test_several_steps 2": [simple_action_step_2]}) as flow:
            flow.validate_actions()
            flow.pass_actions()

        simple_action_step_1._revert_action.assert_called_once()
        simple_action_step_2._revert_action.assert_called_once()

    def test_skip_action(self):
        simple_action = SimpleAction()
        simple_action._revert_action = mock.Mock(return_value=action.ActionResult())
        skip_action = SkipAction()
        skip_action._revert_action = mock.Mock(return_value=action.ActionResult())

        with RevertActionsFlowForTests({"test_skip_action": [simple_action, skip_action]}) as flow:
            flow.validate_actions()
            flow.pass_actions()

        simple_action._revert_action.assert_called_once()
        skip_action._revert_action.assert_not_called()

    def test_revert_pass_based_on_success_saved_state(self):
        check_saved_state("revert", "test_revert_pass_based_on_success_saved_state", "success", True)

    def test_revert_skip_based_on_skip_saved_state(self):
        check_saved_state("revert", "test_revert_skip_based_on_skip_saved_state", "skip", False)

    def test_revert_skip_based_on_failed_saved_state(self):
        check_saved_state("revert", "test_revert_skip_based_on_failed_saved_state", "failed", False)


class TrueCheckAction(action.CheckAction):
    def __init__(self):
        self.name = "true"
        self.description = "Always returns true"

    def _do_check(self):
        return True


class FalseCheckAction(action.CheckAction):
    def __init__(self):
        self.name = "false"
        self.description = "Always returns false"

    def _do_check(self):
        return False


class TestCheckFlow(TestCase):
    def test_true_check(self):
        check_action = TrueCheckAction()
        with action.CheckFlow([check_action]) as flow:
            flow.validate_actions()
            res = flow.make_checks()
            self.assertEqual(len(res), 0)

    def test_several_true(self):
        checks = []
        for _ in range(5):
            checks.append(TrueCheckAction())

        with action.CheckFlow(checks) as flow:
            flow.validate_actions()
            res = flow.make_checks()
            self.assertEqual(len(res), 0)

    def test_several_checks_with_one_false(self):
        checks = []
        checks.append(FalseCheckAction())
        for _ in range(5):
            checks.append(TrueCheckAction())

        with action.CheckFlow(checks) as flow:
            flow.validate_actions()
            res = flow.make_checks()
            self.assertEqual(len(res), 1)

    def test_several_checks_with_several_false(self):
        checks = []
        for _ in range(5):
            checks.append(FalseCheckAction())
        for _ in range(5):
            checks.append(TrueCheckAction())

        with action.CheckFlow(checks) as flow:
            flow.validate_actions()
            res = flow.make_checks()
            self.assertEqual(len(res), 5)
