import json
from uuid import uuid4

import streamlit as st
import streamlit_flow as sf
import streamlit_pydantic as sp

from app.models.action_condition import ComparisonMethod
from app.models.action_condition_operator import LogicalOperator
from app.models.action_param import ActionParamType, LiteralValue
from ui import api, sockets
from ui.models import Action, ActionParam, Agent, Condition, Operator

st.set_page_config(layout="wide")

st.header("Actions")


def save_action(updated_action: dict, triggered_agent: Agent | None) -> None:
    updated_action["triggered_agent_id"] = (
        triggered_agent.id if triggered_agent else None
    )
    updated_action = api.update_action(updated_action)
    if updated_action:
        # api.get_actions.clear()
        st.toast("Action saved successfully.", icon=":material/done:")


def save_action_param(updated_param: dict) -> None:
    updated_param = api.update_action_param(updated_param)
    if updated_param:
        # api.get_actions.clear()
        st.toast("Parameter saved successfully.", icon=":material/done:")


@st.dialog("Add action")
def add_action_dialog():
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

    if st.button("Submit", disabled=not action_name):
        action_dict = {
            "name": action_name,
            "description": action_description,
            "triggered_agent_id": triggered_agent.id,
        }
        created_action = api.create_action(action_dict)
        if created_action:
            # api.get_actions.clear()
            st.toast("Action added successfully.", icon=":material/done:")
            st.rerun()


def param_literal_values(
    param_type: ActionParamType,
    value: list[LiteralValue] | None = None,
    key: str | None = None,
) -> list[LiteralValue] | None:
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

    return literal_values


@st.dialog("Add parameter")
def add_param_dialog(action_id: int) -> None:
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
            # api.get_actions.clear()
            st.toast("Parameter added successfully.", icon=":material/done:")
            st.rerun()


def render_action_param(param: ActionParam) -> None:
    with st.container(border=True, key=f"param_{param.id}"):
        form_model = param.to_form_model()
        updated_param = sp.pydantic_input(f"param_{param.id}", form_model)
        literal_values = param_literal_values(
            updated_param["type"],
            param.literal_values,
            key=f"literal_values_{param.id}",
        )

        save_col, delete_col = st.columns([1, 13])

        with save_col:
            save_param_button = st.button(
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
            if save_param_button:
                updated_param["literal_values"] = literal_values
                save_action_param(updated_param)

        with delete_col:
            delete_param_button = st.button(
                "Delete", key=f"delete_param_{param.id}", icon=":material/delete:"
            )
            if delete_param_button:
                deleted = api.delete_action_param(param.id)
                if deleted:
                    # api.get_actions.clear()
                    st.toast("Parameter deleted successfully.", icon=":material/done:")
                    st.rerun()


def render_action(action: Action) -> None:
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

        show_parameters = st.toggle(
            "Show parameters",
            help="Whether to show the parameters of the action.",
            key=f"show_params_{action.id}",
        )
        if show_parameters:
            for param in action.params:
                render_action_param(param)

            add_param = st.button(
                "Add parameter", key=f"add_param_{action.id}", icon=":material/add:"
            )
            if add_param:
                add_param_dialog(action.id)

        show_conditions = st.toggle(
            "Show conditions",
            help="Whether to show the conditions of the action.",
            key=f"show_conditions_{action.id}",
        )
        if show_conditions:
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
                            id=0,
                            root_id=0,
                            parent_id=None,
                            action_id=action.id,
                            logical_operator=LogicalOperator.OR,
                        )
                        st.session_state[f"flow_state_{action.id}"] = (
                            sf.StreamlitFlowState(
                                nodes=[root.to_node(node_id=str(uuid4()))],
                                edges=[],
                            )
                        )
                        st.rerun()
                else:
                    render_condition_tree(action.id, None)

        save_col, delete_col = st.columns([1, 13])

        with save_col:
            save_button = st.button(
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

        with delete_col:
            delete_button = st.button(
                "Delete", key=f"delete_{action.id}", icon=":material/delete:"
            )
            if delete_button:
                deleted = api.delete_action(action.id)
                if deleted:
                    # api.get_actions.clear()
                    st.toast("Action deleted successfully.", icon=":material/done:")
                    st.rerun()


@st.dialog("Add condition")
def add_condition_dialog(action_id: int):
    agent = None
    if st.toggle(
        "Agent variable",
        help="Whether this condition is based on an agent state variable.",
    ):
        agent = st.selectbox(
            "Agent",
            options=agents,
            format_func=lambda a: a.name,
            help="The agent to use for the condition.",
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
            id=0,
            root_id=0,
            parent_id=0,
            state_variable_name=(
                f"agent-{agent.id}/{state_variable}"
                if agent
                else f"global/{state_variable}"
            ),
            comparison=comparison,
            expected_value=expected_value,
        )
        st.session_state[f"flow_state_{action_id}"].nodes.append(
            condition.to_node(node_id=str(uuid4()))
        )
        st.session_state[f"is_saved_{action_id}"] = False
        st.rerun()


@st.dialog("Edit node")
def edit_node_dialog(action_id: int, node: sf.StreamlitFlowNode) -> None:
    print("Rendering dialog")
    if node.data["type"] == "condition":
        condition = Condition.model_validate(node.data)

        prefix, state_variable_name = condition.state_variable_name.split("/", 1)
        agent_id = int(prefix.split("-")[1]) if prefix.startswith("agent") else None
        agent_variable_toggle = st.toggle(
            "Agent variable",
            value=agent_id is not None,
            help="Whether this condition is based on an agent state variable.",
        )
        if agent_variable_toggle:
            agent = st.selectbox(
                "Agent",
                options=agents,
                format_func=lambda a: a.name,
                index=(
                    agents.index(
                        next(agent for agent in agents if agent.id == agent_id)
                    )
                    if agent_id
                    else 0
                ),
                help="The agent to use for the condition.",
                placeholder="Select an agent",
            )
            agent_id = agent.id

        state = (
            sockets.get_global_state()
            if not agent_id and not agent_variable_toggle
            else sockets.get_agent_state(agent_id)
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
            if agent_id and agent_variable_toggle
            else f"global/{state_variable}"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button(
                "Submit",
                disabled=(
                    state_variable_name == condition.state_variable_name
                    and expected_value == condition.expected_value
                    and comparison == condition.comparison
                ),
            ):
                condition = Condition(
                    id=condition.id,
                    root_id=condition.root_id,
                    parent_id=condition.parent_id,
                    state_variable_name=state_variable_name,
                    comparison=comparison,
                    expected_value=expected_value,
                )
                st.session_state[f"flow_state_{action_id}"].nodes[
                    st.session_state[f"flow_state_{action_id}"].nodes.index(node)
                ] = condition.to_node(
                    node_id=node.id, position=(node.position["x"], node.position["y"])
                )
                st.session_state[f"is_saved_{action_id}"] = False
                st.session_state.node_edited = True
                st.rerun()

        with col2:
            if st.button("Delete", icon=":material/delete:"):
                st.session_state[f"flow_state_{action_id}"].nodes.remove(node)
                st.session_state[f"is_saved_{action_id}"] = False
                st.session_state.node_edited = True
                st.rerun()

    else:
        operator = Operator.model_validate(node.data)
        logical_operator = st.selectbox(
            "Logical operator",
            options=[operator.value for operator in LogicalOperator],
            index=list(LogicalOperator).index(operator.logical_operator),
            help="The logical operator.",
            placeholder="Select a logical operator",
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button(
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
                    st.session_state[f"flow_state_{action_id}"].nodes.index(node)
                ] = operator.to_node(
                    node_id=node.id, position=(node.position["x"], node.position["y"])
                )
                st.session_state[f"is_saved_{action_id}"] = False
                st.session_state.node_edited = True
                st.rerun()

        with col2:
            if st.button(
                "Delete", disabled=operator.is_root(), icon=":material/delete:"
            ):
                st.session_state[f"flow_state_{action_id}"].nodes.remove(node)
                st.session_state[f"is_saved_{action_id}"] = False
                st.session_state.node_edited = True
                st.rerun()


def save_node(parent: Operator, node: sf.StreamlitFlowNode) -> Condition | Operator:
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
    action_id: int, operator: Operator, node: sf.StreamlitFlowNode
) -> None:
    flow_state: sf.StreamlitFlowState = st.session_state[f"flow_state_{action_id}"]

    children_node_ids = [
        edge.target for edge in flow_state.edges if edge.source == node.id
    ]
    children_nodes = [node for node in flow_state.nodes if node.id in children_node_ids]
    for child_node in children_nodes:
        child = save_node(operator, child_node)
        if child_node.data["type"] == "operator":
            save_operator_children(action_id, child, child_node)


def delete_condition_tree(action_id: int) -> None:
    root = next(
        (root for root in condition_tree_roots if root.action_id == action_id),
        None,
    )
    if root is None:
        return

    deleted = api.delete_condition_tree(root.id)
    if deleted:
        # api.get_operators.clear()
        st.toast("Condition tree deleted successfully.", icon=":material/done:")
        del st.session_state[f"flow_state_{action_id}"]
        st.rerun()


def save_condition_tree(action_id: int) -> None:
    root = next(
        (root for root in condition_tree_roots if root.action_id == action_id),
        None,
    )
    if root is not None:
        if not api.delete_condition_tree(root.id):
            return

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

    save_operator_children(action_id, root, root_node)
    st.toast("Condition tree saved successfully.", icon=":material/done:")
    st.session_state[f"is_saved_{action_id}"] = True


@st.fragment
def render_condition_tree(action_id: int, root: Operator | None) -> None:
    print("Rendering tree")
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

    if f"flow_state_{action_id}" not in st.session_state:
        operator_nodes = [operator.to_node() for operator in operators]
        condition_nodes = [condition.to_node() for condition in conditions]
        operator_edges = [
            operator.to_edge() for operator in operators if not operator.is_root()
        ]
        condition_edges = [condition.to_edge() for condition in conditions]

        st.session_state[f"flow_state_{action_id}"] = sf.StreamlitFlowState(
            nodes=operator_nodes + condition_nodes,
            edges=operator_edges + condition_edges,
        )

    if f"is_saved_{action_id}" not in st.session_state:
        st.session_state[f"is_saved_{action_id}"] = True

    with st.container(border=True):
        st.info(
            "- Add new conditions and operators to the condition tree with the button below.\n"  # noqa: E501
            "- Click on a node to edit its properties or delete it.\n"
            "- Click on an edge and press backspace to delete it."
        )
        add_col, evaluate_col, evaluation_result_col = st.columns(
            [1, 1, 7], vertical_alignment="center"
        )
        with add_col:
            with st.popover(
                "Add node",
                icon=":material/add:",
                help="Add a condition or operator to the flow.",
            ):
                c1, c2, c3 = st.columns([1.133, 1.402, 1.301])

                with c1:
                    if st.button("Condition", key=f"add_condition_{action_id}"):
                        add_condition_dialog(action_id)

                with c2:
                    if st.button("**AND** operator", key=f"add_and_{action_id}"):
                        operator = Operator(
                            id=0,
                            root_id=0,
                            parent_id=0,
                            action_id=0,
                            logical_operator=LogicalOperator.AND,
                        )
                        st.session_state[f"flow_state_{action_id}"].nodes.append(
                            operator.to_node(node_id=str(uuid4()))
                        )
                        st.session_state[f"is_saved_{action_id}"] = False
                        st.rerun()

                with c3:
                    if st.button("**OR** operator", key=f"add_or_{action_id}"):
                        operator = Operator(
                            id=-1,
                            root_id=0,
                            parent_id=0,
                            action_id=0,
                            logical_operator=LogicalOperator.OR,
                        )
                        st.session_state[f"flow_state_{action_id}"].nodes.append(
                            operator.to_node(node_id=str(uuid4()))
                        )
                        st.session_state[f"is_saved_{action_id}"] = False
                        st.rerun()

        with evaluate_col:
            if st.button(
                "Evaluate",
                key=f"evaluate_{action_id}",
                disabled=not st.session_state[f"is_saved_{action_id}"],
                icon=":material/play_arrow:",
                help=(
                    "Evaluate the condition tree."
                    if st.session_state[f"is_saved_{action_id}"]
                    else "Save the condition tree before evaluating."
                ),
            ):
                result = api.evaluate_action_conditions(action_id)
                if result is not None:
                    st.session_state[f"evaluation_result_{action_id}"] = result

        with evaluation_result_col:
            result = st.session_state.get(f"evaluation_result_{action_id}")
            if result is not None:
                st.write(f"**Evaluation result:** `{result}`")

        st.session_state[f"flow_state_{action_id}"] = sf.streamlit_flow(
            key=f"condition_tree_flow_{action_id}",
            state=st.session_state[f"flow_state_{action_id}"],
            fit_view=True,
            hide_watermark=True,
            show_controls=False,
            layout=sf.layouts.TreeLayout(direction="down"),
            get_node_on_click=True,
            allow_new_edges=True,
            animate_new_edges=True,
        )

        save_col, delete_col = st.columns([1, 13])
        with save_col:
            if st.button(
                "Save",
                key=f"save_condition_{action_id}",
                icon=":material/save:",
            ):
                save_condition_tree(action_id)

        with delete_col:
            if st.button(
                "Delete condition tree",
                key=f"delete_condition_{action_id}",
                icon=":material/delete:",
            ):
                delete_condition_tree(action_id)

    if st.session_state[f"flow_state_{action_id}"].selected_id:
        if "node_edited" in st.session_state and st.session_state.node_edited:
            st.session_state.node_edited = False
            return

        node = next(
            (
                node
                for node in st.session_state[f"flow_state_{action_id}"].nodes
                if node.id == st.session_state[f"flow_state_{action_id}"].selected_id
            ),
            None,
        )
        if node:
            edit_node_dialog(action_id, node)


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
