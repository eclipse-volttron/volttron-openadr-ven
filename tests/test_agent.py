import os

import openleadr

from volttron_openadr_ven.agent import OpenADRVenAgent, ven_agent


def test_agent_should_create_openadrven_client():
    agent = OpenADRVenAgent("test_ven", "https://fakevtnserver.com")
    assert isinstance(agent.ven_client, openleadr.client.OpenADRClient)


def test_ven_agent_wrapper_should_create_openadrven_client():
    agent = ven_agent(os.path.join(os.getcwd(), "config_test.json"))
    assert isinstance(agent.ven_client, openleadr.client.OpenADRClient)


# Integration tests
# TODO: Implement test when volttron-testing package is created
# def test_on_start_should_publish_event_to_volttron():
#     pass
