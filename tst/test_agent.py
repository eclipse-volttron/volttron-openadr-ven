import os
from unittest import mock

from volttron.platform.vip.agent import Agent

from src.agent import OpenADRVenAgent, ven_agent


class AgentMock(object):
    """
    The purpose for this parent class is to be used for unit
    testing of agents. It takes in the class methods of other
    classes, turns them into it's own mock methods. For testing,
    dynamically replace the agent's current base class with this
    class, while passing in the agent's current classes as arguments.
    For example:
        Agent_to_test.__bases__ = (AgentMock.imitate(Agent, Agent()), )
    As noted in the example, __bases__ takes in a tuple.
    Also, the parent class Agent is passed as both Agent and the
    instantiated Agent(), since it contains a class within it
    that needs to be mocked as well
    """

    @classmethod
    def imitate(cls, *others):
        for other in others:
            for name in other.__dict__:
                try:
                    setattr(cls, name, mock.create_autospec(other.__dict__[name]))
                except (TypeError, AttributeError):
                    pass
        return cls


OpenADRVenAgent.__bases__ = (AgentMock.imitate(Agent, Agent()),)


def test_ven_agent_should_create_OpenADRVenAgent():
    expected_config = {"ven_name": "test_ven"}
    # actual_agent = ven_agent(os.path.join(os.getcwd(), "test_config.json"))
    actual_agent = OpenADRVenAgent("test_ven", None, None, None, None, None, None, None)
    assert actual_agent.ven_name == expected_config["ven_name"]
