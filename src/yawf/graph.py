import pygraphviz


def build_actions_graph(workflow):

    g = pygraphviz.AGraph(directed=True, strict=False)

    for state in workflow._valid_states:
        g.add_node(state)

    for (state_from, state_to, message), action in workflow._actions.iteritems():
        g.add_edge(state_from, state_to, message)
        e = g.get_edge(state_from, state_to, message)
        e.attr['label'] = message

    for (state_to, message), action in workflow._actions_any_startpoint.iteritems():
        for state_from in workflow.get_nonfinal_states():
            g.add_edge(state_from, state_to, message)
            e = g.get_edge(state_from, state_to, message)
            e.attr['label'] = message
            e.attr['color'] = 'gray'

    for (state_from, message), action in workflow._actions_any_destination.iteritems():
        for state_to in workflow._valid_states:
            g.add_edge(state_from, state_to, message)
            e = g.get_edge(state_from, state_to, message)
            e.attr['label'] = message
            e.attr['color'] = 'gray'

    return g


def build_handlers_graph(workflow):

    g = pygraphviz.AGraph(directed=True, strict=False)

    for state in workflow._valid_states:
        g.add_node(state)

    unknown_color = 'gray'
    g.add_node('?')
    unknown_state = g.get_node('?')
    unknown_state.attr['color'] = unknown_color

    for state_from, state_lookup in workflow.get_handlers().iteritems():
        for message, handler in state_lookup.iteritems():
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
