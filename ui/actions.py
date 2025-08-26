import json
from uuid import uuid4

import streamlit as st
import streamlit_flow as sf
import streamlit_pydantic as sp

from app.models.action_condition import ComparisonMethod
from app.models.action_condition_operator import LogicalOperator
from app.models.action_param import ActionParamType, LiteralValue

st.set_page_config(layout="wide")

from ui import api, sockets  # noqa: E402
from ui.models import Action, ActionParam, Agent, Condition, Operator  # noqa: E402
from ui.utils import (  # noqa: E402
    hide_streamlit_menu,
    redirect_if_not_logged_in,
    set_horizontal_buttons_width,
)

redirect_if_not_logged_in()
hide_streamlit_menu()
set_horizontal_buttons_width()


def save_action(updated_action: dict, triggered_agent: Agent | None) -> None:
    """Saves the updated action."""

    updated_action["triggered_agent_id"] = (
        triggered_agent.id if triggered_agent else None
    )
    updated_action = api.update_action(updated_action)
    if updated_action:
        api.get_actions.clear()
        st.toast("Action saved successfully.", icon=":material/done:")


def save_action_param(updated_param: dict) -> None:
    """Saves the updated action parameter."""

    updated_param = api.update_action_param(updated_param)
    if updated_param:
        api.get_actions.clear()
        st.toast("Parameter saved successfully.", icon=":material/done:")


@st.dialog("Add action")
def add_action_dialog():
    """Renders a dialog to create a new action."""

    action_name = st.text_input("Name", help="The name of the action.")
    action_description = st.text_area(
        "Description", help="A description of the action."
    )

    triggered_agent = None
    triggers_agent_toggle = st.toggle(
        "Triggers agent",
        help="Whether this action triggers an agent.",
    )
    if triggers_agent_toggle:
        triggered_agent = st.selectbox(
            "Triggered agent",
            options=agents,
            format_func=lambda agent: agent.name,
            help="Optional agent that is triggered by this action.",
            placeholder="Select an agent",
        )
        st.info(
            "Make sure to add parameters to actions which trigger other agents.\n\n"
            "For example a 'question' string parameter for the agent to receive information."  # noqa: E501
        )

    if st.button("Submit", disabled=not action_name):
        if any(a.name == action_name for a in actions):
            st.error(
                "An action with this name already exists!",
                icon=":material/error:",
            )
            return

        action_dict = {
            "name": action_name,
            "description": action_description,
            "triggered_agent_id": triggered_agent.id if triggered_agent else None,
        }
        created_action = api.create_action(action_dict)
        if created_action:
            api.get_actions.clear()
            st.toast("Action added successfully.", icon=":material/done:")
            st.rerun()


def param_literal_values(
    param_type: ActionParamType,
    value: list[LiteralValue] | None = None,
    key: str | None = None,
) -> list[LiteralValue] | None:
    """Renders the literal values input for a parameter."""

    literal_values = None
    if param_type == "literal":
        literal_values_text = st.text_input(
            "Literal values",
            value=json.dumps(value) if value is not None else None,
            help=(
                "The literal values of the parameter in JSON array format.\n\n"
                'Example: ["text", 123, true, null, 3.14]'
            ),
            placeholder="Enter the literal values as a JSON array",
            key=key,
        )
        if literal_values_text:
            try:
                literal_values = json.loads(literal_values_text)
                if not isinstance(literal_values, list):
                    literal_values = None
                    st.toast(
                        "Invalid JSON format for literal values.",
                        icon=":material/error:",
                    )
            except json.JSONDecodeError:
                st.toast(
                    "Invalid JSON format for literal values.", icon=":material/error:"
                )

    if isinstance(literal_values, list) and not literal_values:
        st.toast("Literal values cannot be empty.", icon=":material/error:")

    return literal_values


@st.dialog("Add parameter")
def add_param_dialog(action_id: int) -> None:
    """Renders a dialog to create a new parameter for an action."""

    param_name = st.text_input("Name", help="The name of the parameter.")
    param_description = st.text_area(
        "Description", help="A description of the parameter."
    )
    param_type = st.selectbox(
        "Type",
        options=["str", "int", "float", "bool", "literal"],
        help="The type of the parameter.",
        placeholder="Select a type",
    )
    literal_values = param_literal_values(param_type)

    submit = st.button(
        "Submit",
        disabled=(param_type == "literal" and not literal_values) or not param_name,
    )
    if submit:
        param_dict = {
            "action_id": action_id,
            "name": param_name,
            "description": param_description,
            "type": param_type,
            "literal_values": literal_values,
        }
        created_param = api.create_action_param(param_dict)
        if created_param:
            api.get_actions.clear()
            st.toast("Parameter added successfully.", icon=":material/done:")
            st.rerun()


def render_action_param(param: ActionParam) -> None:
    """Renders an action parameter's details."""

    with st.container(border=True, key=f"param_{param.id}"):
        form_model = param.to_form_model()
        updated_param = sp.pydantic_input(f"param_{param.id}", form_model)
        literal_values = param_literal_values(
            updated_param["type"],
            param.literal_values,
            key=f"literal_values_{param.id}",
        )

        save_col, delete_col = st.columns(2)

        save_button = save_col.button(
            "Save",
            disabled=(
                (updated_param["type"] == "literal" and not literal_values)
                or (
                    updated_param == form_model.model_dump()
                    and literal_values == param.literal_values
                )
                or not updated_param["name"]
            ),
            key=f"save_param_{param.id}",
            icon=":material/save:",
            type="primary",
        )
        if save_button:
            updated_param["literal_values"] = literal_values
            save_action_param(updated_param)

        delete_button = delete_col.button(
            "Delete", key=f"delete_param_{param.id}", icon=":material/delete:"
        )
        if delete_button:
            deleted = api.delete_action_param(param.id)
            if deleted:
                api.get_actions.clear()
                st.toast("Parameter deleted successfully.", icon=":material/done:")
                st.rerun()


def render_action_conditions(action: Action) -> None:
    """
    Renders an action's conditions or a button to create
    new condition tree with a root node only.
    """

    root = next(
        (root for root in condition_tree_roots if root.action_id == action.id),
        None,
    )
    if root:
        render_condition_tree(action.id, root)
    else:
        if f"flow_state_{action.id}" not in st.session_state:
            if st.button(
                "Create condition tree",
                key=f"create_condition_tree_{action.id}",
                icon=":material/add:",
            ):
                root = Operator(
                    parent_id=None,
                    action_id=action.id,
                    logical_operator=LogicalOperator.OR,
                )
                st.session_state[f"flow_state_{action.id}"] = sf.StreamlitFlowState(
                    nodes=[root.to_node(node_id=str(uuid4()))],
                    edges=[],
                )
                st.rerun()
        else:
            render_condition_tree(action.id, None)


def render_action(action: Action) -> None:
    """Renders an action's details, parameters and conditions."""

    with st.expander(action.name):
        updated_action = sp.pydantic_input(
            f"action_{action.id}", action.to_form_model()
        )

        triggered_agent = None
        triggers_agent_toggle = st.toggle(
            "Triggers agent",
            value=action.triggered_agent_id is not None,
            help="Whether this action triggers an agent.",
            key=f"toggle_{action.id}",
        )
        if triggers_agent_toggle:
            triggered_agent = next(
                (agent for agent in agents if agent.id == action.triggered_agent_id),
                None,
            )
            triggered_agent = st.selectbox(
                "Triggered agent",
                options=agents,
                format_func=lambda agent: agent.name,
                index=agents.index(triggered_agent) if triggered_agent else None,
                help="Optional agent that is triggered by this action.",
                placeholder="Select an agent",
                key=f"triggered_agent_{action.id}",
            )
            st.info(
                "Make sure to add parameters to actions which trigger other agents.\n\n"
                "For example a 'question' string parameter for the agent to receive information."  # noqa: E501
            )

        show_parameters = st.toggle("Show parameters", key=f"show_params_{action.id}")
        if show_parameters:
            for param in action.params:
                render_action_param(param)

            add_param = st.button(
                "Add parameter", key=f"add_param_{action.id}", icon=":material/add:"
            )
            if add_param:
                add_param_dialog(action.id)

        show_conditions = st.toggle(
            "Show conditions", key=f"show_conditions_{action.id}"
        )
        if show_conditions:
            render_action_conditions(action)

        save_col, delete_col = st.columns(2)

        save_button = save_col.button(
            "Save",
            disabled=(
                (
                    updated_action == action.to_form_model().model_dump()
                    or not updated_action["name"]
                )
                and (triggered_agent.id if triggered_agent else None)
                == action.triggered_agent_id
            ),
            key=f"save_{action.id}",
            icon=":material/save:",
            type="primary",
        )
        if save_button:
            save_action(updated_action, triggered_agent)

        delete_button = delete_col.button(
            "Delete", key=f"delete_{action.id}", icon=":material/delete:"
        )
        if delete_button:
            deleted = api.delete_action(action.id)
            if deleted:
                api.get_actions.clear()
                st.toast("Action deleted successfully.", icon=":material/done:")
                st.rerun()


@st.dialog("Add condition")
def add_condition_dialog(action_id: int):
    """Renders a dialog to create a new condition node."""

    agent = None
    if st.toggle(
        "Agent variable",
        help="Whether this condition is based on an agent state variable.",
    ):
        agent = st.selectbox(
            "Agent",
            options=agents,
            format_func=lambda a: a.name,
            help="The agent whose state variable to use for the condition.",
            placeholder="Select an agent",
        )

    state = (
        sockets.get_global_state() if not agent else sockets.get_agent_state(agent.id)
    )

    state_variable = st.selectbox(
        "State variable",
        options=state.keys(),
        help="The name of the state variable.",
        placeholder="Select a state variable",
    )
    comparison = st.selectbox(
        "Comparison",
        options=[comparison.value for comparison in ComparisonMethod],
        help="The comparison method.",
        placeholder="Select a comparison",
    )
    expected_value = st.text_input(
        "Expected value",
        help=(
            "The expected value of the state variable.\n\n"
            "Type is inferred from the value based on JSON format."
        ),
    )

    if st.button("Submit", disabled=not state_variable or not expected_value):
        condition = Condition(
            state_variable_name=(
                f"agent-{agent.id}/{state_variable}"
                if agent
                else f"global/{state_variable}"
            ),
            comparison=comparison,
            expected_value=expected_value,
        )
        st.session_state[f"flow_state_{action_id}"].nodes.append(
            condition.to_node(node_id=str(uuid4()), agent=agent)
        )
        st.session_state[f"is_saved_{action_id}"] = False
        st.rerun()


def _get_node_index_by_id(action_id: int, node_id: str) -> int:
    """Returns the index of a node by its ID in the flow state."""

    return next(
        i
        for i, n in enumerate(st.session_state[f"flow_state_{action_id}"].nodes)
        if n.id == node_id
    )


def edit_condition_node(action_id: int, node: sf.StreamlitFlowNode) -> None:
    """Renders a dialog to edit a condition node."""

    condition = Condition.model_validate(node.data)

    prefix, state_variable_name = condition.state_variable_name.split("/", 1)
    agent_id = int(prefix.split("-")[1]) if prefix.startswith("agent") else None

    current_agent = (
        next((agent for agent in agents if agent.id == agent_id), None)
        if agent_id
        else None
    )

    agent_variable_toggle = st.toggle(
        "Agent variable",
        value=agent_id is not None,
        help="Whether this condition is based on an agent state variable.",
    )
    agent = None
    if agent_variable_toggle:
        agent = st.selectbox(
            "Agent",
            options=agents,
            format_func=lambda a: a.name,
            index=(agents.index(current_agent) if current_agent else 0),
            help="The agent whose state variable to use for the condition.",
            placeholder="Select an agent",
        )
        agent_id = agent.id

    is_agent_state = agent_id and agent_variable_toggle
    state = (
        sockets.get_agent_state(agent_id)
        if is_agent_state
        else sockets.get_global_state()
    )

    try:
        index = list(state.keys()).index(state_variable_name)
    except ValueError:
        index = 0

    state_variable = st.selectbox(
        "State variable",
        options=state.keys(),
        index=index,
        help="The name of the state variable.",
        placeholder="Select a state variable",
    )
    comparison = st.selectbox(
        "Comparison",
        options=[comparison.value for comparison in ComparisonMethod],
        index=list(ComparisonMethod).index(condition.comparison),
        help="The comparison method.",
        placeholder="Select a comparison",
    )
    expected_value = st.text_input(
        "Expected value",
        value=condition.expected_value,
        help=(
            "The expected value of the state variable.\n\n"
            "Type is inferred from the value based on JSON format."
        ),
    )

    state_variable_name = (
        f"agent-{agent_id}/{state_variable}"
        if is_agent_state
        else f"global/{state_variable}"
    )

    submit_col, delete_col = st.columns(2)

    submit_button = submit_col.button(
        "Submit",
        disabled=(
            state_variable_name == condition.state_variable_name
            and expected_value == condition.expected_value
            and comparison == condition.comparison
        ),
    )
    if submit_button:
        condition = Condition(
            id=condition.id,
            root_id=condition.root_id,
            parent_id=condition.parent_id,
            state_variable_name=state_variable_name,
            comparison=comparison,
            expected_value=expected_value,
        )
        st.session_state[f"flow_state_{action_id}"].nodes[
            _get_node_index_by_id(action_id, node.id)
        ] = condition.to_node(
            node_id=node.id,
            position=(node.position["x"], node.position["y"]),
            agent=agent,
        )
        st.session_state[f"is_saved_{action_id}"] = False
        st.session_state.node_edited = True
        st.rerun()

    if delete_col.button("Delete", icon=":material/delete:"):
        st.session_state[f"flow_state_{action_id}"].nodes.remove(node)
        st.session_state[f"is_saved_{action_id}"] = False
        st.session_state.node_edited = True
        st.rerun()


def edit_operator_node(action_id: int, node: sf.StreamlitFlowNode) -> None:
    """Renders a dialog to edit an operator node."""

    operator = Operator.model_validate(node.data)
    logical_operator = st.selectbox(
        "Logical operator",
        options=[operator.value for operator in LogicalOperator],
        index=list(LogicalOperator).index(operator.logical_operator),
        help="The logical operator.",
        placeholder="Select a logical operator",
    )

    submit_col, delete_col = st.columns(2)

    if submit_col.button(
        "Submit", disabled=logical_operator == operator.logical_operator
    ):
        operator = Operator(
            id=operator.id,
            root_id=operator.root_id,
            parent_id=operator.parent_id,
            action_id=operator.action_id,
            logical_operator=logical_operator,
        )
        st.session_state[f"flow_state_{action_id}"].nodes[
            _get_node_index_by_id(action_id, node.id)
        ] = operator.to_node(
            node_id=node.id, position=(node.position["x"], node.position["y"])
        )
        st.session_state[f"is_saved_{action_id}"] = False
        st.session_state.node_edited = True
        st.rerun()

    if delete_col.button(
        "Delete", disabled=operator.is_root(), icon=":material/delete:"
    ):
        st.session_state[f"flow_state_{action_id}"].nodes.remove(node)
        st.session_state[f"is_saved_{action_id}"] = False
        st.session_state.node_edited = True
        st.rerun()


@st.dialog("Edit node")
def edit_node_dialog(action_id: int, node: sf.StreamlitFlowNode) -> None:
    """Renders a dialog to edit a condition or operator node."""

    if node.data["type"] == "condition":
        edit_condition_node(action_id, node)
    else:
        edit_operator_node(action_id, node)


def save_node(parent: Operator, node: sf.StreamlitFlowNode) -> Condition | Operator:
    """Saves a condition or operator node."""

    if node.data["type"] == "condition":
        condition = Condition.model_validate(node.data)
        condition.parent_id = parent.id
        condition.root_id = parent.root_id

        return api.create_condition(condition)
    else:
        operator = Operator.model_validate(node.data)
        operator.parent_id = parent.id
        operator.root_id = parent.root_id
        operator.action_id = parent.action_id

        return api.create_operator(operator)


def save_operator_children(
    flow_state: sf.StreamlitFlowState, operator: Operator, node: sf.StreamlitFlowNode
) -> None:
    """Recursively saves the children of an operator node."""

    children_node_ids = [
        edge.target for edge in flow_state.edges if edge.source == node.id
    ]
    children_nodes = [node for node in flow_state.nodes if node.id in children_node_ids]
    for child_node in children_nodes:
        child = save_node(operator, child_node)
        if child_node.data["type"] == "operator":
            save_operator_children(flow_state, child, child_node)


def save_condition_tree(action_id: int) -> None:
    """Saves the condition tree of an action."""

    root = next(
        (root for root in condition_tree_roots if root.action_id == action_id),
        None,
    )
    if root is not None:
        if not api.delete_condition_tree(root.id):
            return

        api.get_operators.clear()
        api.get_conditions.clear()

    flow_state: sf.StreamlitFlowState = st.session_state[f"flow_state_{action_id}"]

    root_node = next((node for node in flow_state.nodes if node.type == "input"), None)
    if root_node is None:
        st.toast("Did not find a root node.", icon=":material/error:")
        return

    root = api.create_condition_tree(
        {"action_id": action_id, "logical_operator": root_node.data["logical_operator"]}
    )
    if not root:
        return

    save_operator_children(flow_state, root, root_node)
    api.get_operators.clear()
    api.get_conditions.clear()
    st.toast("Condition tree saved successfully.", icon=":material/done:")
    st.session_state[f"is_saved_{action_id}"] = True
    if f"evaluation_result_{action_id}" in st.session_state:
        del st.session_state[f"evaluation_result_{action_id}"]

    st.rerun()


def delete_condition_tree(action_id: int) -> None:
    """Deletes the condition tree of an action."""

    root = next(
        (root for root in condition_tree_roots if root.action_id == action_id),
        None,
    )
    if root is None:
        return

    deleted = api.delete_condition_tree(root.id)
    if deleted:
        api.get_operators.clear()
        api.get_conditions.clear()
        st.toast("Condition tree deleted successfully.", icon=":material/done:")
        del st.session_state[f"flow_state_{action_id}"]
        if f"is_saved_{action_id}" in st.session_state:
            del st.session_state[f"is_saved_{action_id}"]
        if f"evaluation_result_{action_id}" in st.session_state:
            del st.session_state[f"evaluation_result_{action_id}"]
        st.rerun()


def get_agent_for_condition(conditiion: Condition) -> Agent | None:
    """Returns the agent for a condition."""

    if conditiion.state_variable_name.startswith("global"):
        return None

    agent_id = int(conditiion.state_variable_name.split("/", 1)[0].split("-")[1])
    return next((agent for agent in agents if agent.id == agent_id), None)


@st.fragment
def render_condition_tree(action_id: int, root: Operator | None) -> None:
    """Renders the condition tree of an action."""

    flow_state_key = f"flow_state_{action_id}"
    is_saved_key = f"is_saved_{action_id}"

    if root is not None:
        conditions = [
            condition for condition in all_conditions if condition.root_id == root.id
        ]
        operators = [
            operator for operator in all_operators if operator.root_id == root.id
        ]
    else:
        conditions = []
        operators = []

    if flow_state_key not in st.session_state:
        operator_nodes = [operator.to_node() for operator in operators]
        condition_nodes = [
            condition.to_node(agent=get_agent_for_condition(condition))
            for condition in conditions
        ]
        operator_edges = [
            operator.to_edge() for operator in operators if not operator.is_root()
        ]
        condition_edges = [condition.to_edge() for condition in conditions]

        st.session_state[flow_state_key] = sf.StreamlitFlowState(
            nodes=operator_nodes + condition_nodes,
            edges=operator_edges + condition_edges,
        )

    if is_saved_key not in st.session_state:
        st.session_state[is_saved_key] = True

    with st.container(border=True):
        st.info(
            "- Add new conditions and operators to the condition tree with the button below.\n"  # noqa: E501
            "- Click on a node to edit its properties or delete it.\n"
            "- Click on an edge and press backspace to delete it.\n"
            "- You can evaluate the saved condition tree with the Evaluate button."
        )
        add_col, evaluate_col, evaluation_result_col = st.columns(
            3, vertical_alignment="center"
        )
        with add_col.popover(
            "Add node",
            icon=":material/add:",
            help="Add a condition or operator to the flow.",
        ):
            condition_col, and_operator_col, or_operator_col = st.columns(3)

            if condition_col.button("Condition", key=f"add_condition_{action_id}"):
                add_condition_dialog(action_id)

            if and_operator_col.button("**AND** operator", key=f"add_and_{action_id}"):
                operator = Operator(logical_operator=LogicalOperator.AND)
                st.session_state[flow_state_key].nodes.append(
                    operator.to_node(node_id=str(uuid4()))
                )
                st.session_state[is_saved_key] = False
                st.rerun()

            if or_operator_col.button("**OR** operator", key=f"add_or_{action_id}"):
                operator = Operator(logical_operator=LogicalOperator.OR)
                st.session_state[flow_state_key].nodes.append(
                    operator.to_node(node_id=str(uuid4()))
                )
                st.session_state[is_saved_key] = False
                st.rerun()

        evaluate_button = evaluate_col.button(
            "Evaluate",
            key=f"evaluate_{action_id}",
            disabled=not st.session_state[is_saved_key],
            icon=":material/play_arrow:",
            help=(
                "Evaluate the condition tree."
                if st.session_state[is_saved_key]
                else "Save the condition tree before evaluating."
            ),
        )
        if evaluate_button:
            result = api.evaluate_action_conditions(action_id)
            if result is not None:
                st.session_state[f"evaluation_result_{action_id}"] = result

        with evaluation_result_col:
            result = st.session_state.get(f"evaluation_result_{action_id}")
            if result is not None:
                st.write(f"**Evaluation result:** `{result}`")

        st.session_state[flow_state_key] = sf.streamlit_flow(
            key=f"condition_tree_flow_{action_id}",
            state=st.session_state[flow_state_key],
            fit_view=True,
            hide_watermark=True,
            show_controls=False,
            layout=sf.layouts.TreeLayout(direction="down"),
            get_node_on_click=True,
            allow_new_edges=True,
            animate_new_edges=True,
        )

        save_col, delete_col = st.columns(2)

        if save_col.button(
            "Save",
            key=f"save_condition_{action_id}",
            icon=":material/save:",
        ):
            save_condition_tree(action_id)

        if delete_col.button(
            "Delete condition tree",
            key=f"delete_condition_{action_id}",
            icon=":material/delete:",
        ):
            delete_condition_tree(action_id)

    if st.session_state[flow_state_key].selected_id:
        if "node_edited" in st.session_state and st.session_state.node_edited:
            st.session_state.node_edited = False
            return

        node = next(
            (
                node
                for node in st.session_state[flow_state_key].nodes
                if node.id == st.session_state[flow_state_key].selected_id
            ),
            None,
        )
        if node:
            edit_node_dialog(action_id, node)


st.header("Actions")

with st.spinner("Loading..."):
    agents = api.get_agents()
    actions = api.get_actions()
    all_conditions = api.get_conditions()
    all_operators = api.get_operators()
    condition_tree_roots = [
        operator for operator in all_operators if operator.is_root()
    ]
    for action in actions:
        render_action(action)

if st.button("Add action", icon=":material/add:"):
    add_action_dialog()
