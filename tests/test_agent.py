import openleadr

from volttron_openadr_ven.agent import OpenADRVenAgent


def test_agent_should_create_openadrven_client():
    agent = OpenADRVenAgent("test_ven", "https://fakevtnserver.com")
    assert isinstance(agent.ven_client, openleadr.client.OpenADRClient)


# Integration tests
# TODO: Implement test when volttron-testing package is created
# def test_on_start_should_publish_event_to_volttron():
#     pass
