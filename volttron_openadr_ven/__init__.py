# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright 2020, Battelle Memorial Institute.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This material was prepared as an account of work sponsored by an agency of
# the United States Government. Neither the United States Government nor the
# United States Department of Energy, nor Battelle, nor any of their
# employees, nor any jurisdiction or organization that has cooperated in the
# development of these materials, makes any warranty, express or
# implied, or assumes any legal liability or responsibility for the accuracy,
# completeness, or usefulness or any information, apparatus, product,
# software, or process disclosed, or represents that its use would not infringe
# privately owned rights. Reference herein to any specific commercial product,
# process, or service by trade name, trademark, manufacturer, or otherwise
# does not necessarily constitute or imply its endorsement, recommendation, or
# favoring by the United States Government or any agency thereof, or
# Battelle Memorial Institute. The views and opinions of authors expressed
# herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY operated by
# BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
# }}}

# This __init__.py file is a shim that allows the agent to run in either the 8.x version of VOLTTRON
# or the new modular volttron.  The imports are the primary difference and therefore if the
# 8.x version is loaded but the modular version is only available then an import exception will
# be thrown.
#
# If neither are available then an import exception will be thrown.
#
# In order to use this, the agent itself should use this import by using
#
# from . import (
#     get_aware_utc_now,
#     ....
#     ....
# )
#
# This redirects the correct version of the code to either the modular or 8.x version to import.
try:
    # Attempt to import from 8.x version of VOLTTRON if not successful to import then
    # attempt to import from modular version of VOLTTRON.
    from volttron.platform import jsonapi
    from volttron.platform.agent.utils import (
        get_aware_utc_now,
        setup_logging,
        format_timestamp,
        load_config,
        isapipe,
        vip_main,
    )
    from volttron.platform.messaging import topics, headers
    from volttron.platform.vip.agent import Agent, Core, RPC

except ImportError:

    from volttron.utils import (
        get_aware_utc_now,
        jsonapi,
        setup_logging,
        format_timestamp,
        load_config,
        isapipe,
        vip_main,
    )

    from volttron.client.vip.agent import Agent, Core, RPC
    from volttron.client.messaging import topics, headers
