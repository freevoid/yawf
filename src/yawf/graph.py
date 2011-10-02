import pygraphviz


def build_effects_graph(workflow):

    g = pygraphviz.AGraph(directed=True, strict=False)

    for state in workflow._valid_states:
        g.add_node(state)

    for (state_from, state_to, message), _effects in workflow.library.iter_effects():
        g.add_edge(state_from, state_to, message)
        e = g.get_edge(state_from, state_to, message)
        e.attr['label'] = message

    return g

build_actions_graph = build_effects_graph


def build_handlers_graph(workflow):

    g = pygraphviz.AGraph(directed=True, strict=False)

    for state in workflow._valid_states:
        g.add_node(state)

    unknown_color = 'gray'
    g.add_node('?')
    unknown_state = g.get_node('?')
    unknown_state.attr['color'] = unknown_color

    for ((state_from, message), handlers) in workflow.library.iter_handlers():
        for handler in handlers:
            if hasattr(handler, 'is_annotated'):
                if len(handler.states_to) > 1:
                    style = 'dashed'
                else:
                    style = 'solid'

                for state_to in handler.states_to:

                    if state_to == '_':
                        state_to = state_from

                    g.add_edge(state_from, state_to, message)
                    e = g.get_edge(state_from, state_to, message)
                    e.attr['label'] = message
                    e.attr['style'] = style
            else:
                g.add_edge(state_from, unknown_state, message)
                e = g.get_edge(state_from, unknown_state, message)
                e.attr['label'] = message
                e.attr['color'] = unknown_color

    return g
