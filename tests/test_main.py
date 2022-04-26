import pytest
import json

import sys, os
sys.path.append(os.getcwd())
from core.schemas import *

# SESSION
class TestMain:
    
    # @pytest.mark.order(1)
    def test_post_session(self, client, session_id_manager):
        response = client.post("/session")
        assert response.status_code == 200
        response_json = response.json()
        assert isinstance(response_json['session_id'], int)
        session_id_manager.session_id = response_json['session_id']
        assert response_json['session_name'] == 'unnamed'
        assert response_json['log_file'] == 'pyshop_log.py'
        
    def test_post_session2(self, client, session_id_manager):
        response = client.post("/session")
        assert response.status_code == 200
        response_json = response.json()
        assert isinstance(response_json['session_id'], int)
        session_id_manager.session_id = response_json['session_id']
        assert response_json['session_name'] == 'unnamed'
        assert response_json['log_file'] == 'pyshop_log.py'

    # @pytest.mark.order(2)
    def test_get_sessions(self, client, session_id_manager):
        response = client.get("/sessions")
        assert response.status_code == 200

    # @pytest.mark.order(3)
    def test_get_session_that_exists(self, client, session_id_manager):
        response = client.get("/session", params={'session_id': str(session_id_manager.session_id)})
        assert response.status_code == 200
        assert response.json() == {
            'session_id': session_id_manager.session_id,
            'session_name': 'unnamed',
            'log_file': 'pyshop_log.py'
        }

    # @pytest.mark.order(4)
    def test_get_session_that_doesnt_exist(self, client, session_id_manager):
        response = client.get("/session?session_id=42")
        assert response.status_code == 404
        assert response.json() == {
            'detail': 'Session with id {42} not found'
        }

    # TIME RESOLUTION

    # @pytest.mark.order(5)
    def test_get_time_resolution_before_set(self, client, session_id_manager):
        response = client.get("/time_resolution", headers={'session-id': str(session_id_manager.session_id)})
        assert response.status_code == 400
        assert response.json() == {
            'detail': 'First you must set the time_resolution of the session'
        }

    # @pytest.mark.order(6)
    def test_put_time_resolution_missing_body(self, client, session_id_manager):
        response = client.put(
            "/time_resolution",
            headers={'session-id': str(session_id_manager.session_id)},
            data={

            }
        )
        assert response.status_code == 422
        assert response.json() == {
            "detail": [{
                "loc": ["body"],
                "msg": "field required",
                "type": "value_error.missing"
            }]
        }


    # @pytest.mark.order(7)
    def test_put_time_resolution_bad_time_order(self, client, session_id_manager):
        response = client.put(
            "/time_resolution",
            headers={'session-id': str(session_id_manager.session_id)},
            json={
                "start_time": "2021-05-03T00:00:00.00Z",
                "end_time": "2021-05-02T00:00:00.00Z",
                "time_unit": "hour"
            }
        )

        assert response.status_code == 400
        assert response.json() == {'detail': 'end_time must be strictly greater than start_time'}


    # @pytest.mark.order(8)
    def test_put_time_resolution(self, client, session_id_manager):
        response = client.put(
            "/time_resolution",
            headers={'session-id': str(session_id_manager.session_id)},
            json={
                "start_time": "2021-05-02T00:00:00.00Z",
                "end_time": "2021-05-03T00:00:00.00Z",
                "time_unit": "hour"
            }
        )

        assert response.status_code == 200
        assert response.json() == None


    # @pytest.mark.order(9)
    def test_put_time_resolution_invalid_session(self, client, session_id_manager):
        response = client.put(
            "/time_resolution",
            headers={'session-id': '42'},
            json={
                "start_time": "2021-05-02T00:00:00.00Z",
                "end_time": "2021-05-03T00:00:00.00Z",
                "time_unit": "hour"
            }
        )

        assert response.status_code == 400
        assert response.json() == {'detail': 'Session {42} does not exist.'}

        
    # MODEL

    # @pytest.mark.order(10)
    def test_get_model(self, client, session_id_manager):
        response = client.get(
            "/model",
            headers={'session-id': str(session_id_manager.session_id)}
        )
        assert response.status_code == 200
        response_json = response.json()
        assert 'model' in response_json
        assert 'scenario' in response_json['model']
        assert 'objective' in response_json['model']
        assert 'average_objective' in response_json['model']['objective']
        assert 'grand_total' in response_json['model']['objective']['average_objective']

    # @pytest.mark.order(11)
    def test_get_model_object_type_info(self, client, session_id_manager):
        response = client.get(
            "/model/plant/information",
            headers={'session-id': str(session_id_manager.session_id)}
        )
        assert response.status_code == 200
        ot = ObjectType(**response.json())  # Thanks to pydantic this raises exceptions if response is wrong

    # @pytest.mark.order(12)
    def test_get_model_object_instance_nonexistent(self, client, session_id_manager):
        response = client.get(
            '/model/reservoir?object_name=test_res',
            headers={'session-id': str(session_id_manager.session_id)}
        )
        assert response.status_code == 400
        assert response.json() == {
            'detail': 'object_name {test_res} is not an instance of object_type {reservoir}.'
        }

    # @pytest.mark.order(13)
    def test_put_model_object_instance_no_body(self, client, session_id_manager):
        response = client.put(
            '/model/reservoir?object_name=test_res',
            headers={"accept": "application/json","Content-Type": "application/json",'session-id': str(session_id_manager.session_id)}
        )
        assert response.status_code == 200
        o = ObjectInstance(**response.json()) # Thanks to pydantic this raises exceptions if response is wrong

    expected_b = ObjectInstance(
        attributes={
            'vol_head': Curve(**{
                'x_unit': 'MM3', 'y_unit': 'METER',
                'y_values': [42.0, 43.0, 45.0],
                'x_values': [10.0, 20.0, 30.0]
            }),
            'water_value_input': {
                '0.0': Curve(**{
                    'x_unit': 'MM3', 'y_unit': 'NOK/MM3',
                    'x_values': [10.0, 9.0, 8.0],
                    'y_values': [42.0, 20.0, 10.0]
                })
            },
            'inflow': TimeSeries(**{
                'unit': 'M3/S',
                'name': 'inflow',
                'timestamps': [
                    '2021-05-02T00:00:00+00:00',
                    '2021-05-02T01:00:00+00:00',
                    '2021-05-02T02:00:00+00:00',
                    '2021-05-02T03:00:00+00:00',
                    '2021-05-02T04:00:00+00:00',
                    '2021-05-02T05:00:00+00:00',
                    '2021-05-02T06:00:00+00:00',
                    '2021-05-02T07:00:00+00:00',
                    '2021-05-02T08:00:00+00:00',
                    '2021-05-02T09:00:00+00:00',
                    '2021-05-02T10:00:00+00:00',
                    '2021-05-02T11:00:00+00:00',
                    '2021-05-02T12:00:00+00:00',
                    '2021-05-02T13:00:00+00:00',
                    '2021-05-02T14:00:00+00:00',
                    '2021-05-02T15:00:00+00:00',
                    '2021-05-02T16:00:00+00:00',
                    '2021-05-02T17:00:00+00:00',
                    '2021-05-02T18:00:00+00:00',
                    '2021-05-02T19:00:00+00:00',
                    '2021-05-02T20:00:00+00:00',
                    '2021-05-02T21:00:00+00:00',
                    '2021-05-02T22:00:00+00:00',
                    '2021-05-02T23:00:00+00:00'
                ],
                'values': [
                    [
                    42,
                    42,
                    42,
                    42,
                    42,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50,
                    50
                    ]
                ]
            })
        }
    )

    # @pytest.mark.order(14)
    def test_put_model_object_instance_with_body(self, client, session_id_manager):

        a = ObjectInstance(
            # object_name='test_res',
            # object_type='reservoir',
            attributes={
                'vol_head': Curve(**{
                    'y_values': [42.0, 43.0, 45.0],
                    'x_values': [10.0, 20.0, 30.0]
                }),
                'water_value_input': {
                    '0.0': Curve(**{
                        'x_values': [10.0, 9.0, 8.0],
                        'y_values': [42.0, 20.0, 10.0]
                    })
                },
                'inflow': TimeSeries(**{
                    'timestamps': ['2021-05-02T00:00:00Z','2021-05-02T05:00:00Z'],
                    'values': [[42.0, 50.0]]
                })
            }
        )

        response = client.put(
            '/model/reservoir',
            params={'object_name': 'test_res'},
            headers={"accept": "application/json","Content-Type": "application/json", "session-id": str(session_id_manager.session_id)},
            data=a.json()
        )
        assert response.status_code == 200
        b = ObjectInstance(**response.json()) # Thanks to pydantic this raises exceptions if response is wrong
        for attr, expected_value in self.expected_b.attributes.items():
            assert b.attributes[attr] == expected_value

    # @pytest.mark.order(15)
    def test_get_model_object_instance(self, client, session_id_manager):
        response = client.get(
            '/model/reservoir?object_name=test_res',
            headers={"session-id": str(session_id_manager.session_id)}
        )
        assert response.status_code == 200
        b = ObjectInstance(**response.json()) # Thanks to pydantic this raises exceptions if response is wrong
        for attr, expected_value in self.expected_b.attributes.items():
            assert b.attributes[attr] == expected_value

    # @pytest.mark.order(16)
    def test_get_connections_nonexistent(self, client, session_id_manager):
        response = client.get(
            '/connections',
            headers={"session-id": str(session_id_manager.session_id)}
        )
        assert response.status_code == 200
        assert response.json() == []

    # @pytest.mark.order(17)
    def test_put_model_object_instance_reservoir_r1(self, client, session_id_manager):
        response = client.put(
            '/model/reservoir?object_name=r1',
            headers={"session-id": str(session_id_manager.session_id)}
        )
        assert response.status_code == 200
        o = ObjectInstance(**response.json()) # Thanks to pydantic this raises exceptions if response is wrong

    # @pytest.mark.order(18)
    def test_put_model_object_instance_plant_p1(self, client, session_id_manager):
        response = client.put(
            '/model/plant?object_name=p1',
            headers={"session-id": str(session_id_manager.session_id)}
        )
        assert response.status_code == 200
        o = ObjectInstance(**response.json()) # Thanks to pydantic this raises exceptions if response is wrong

    # @pytest.mark.order(19)
    def test_put_connections(self, client, session_id_manager):
        response = client.put(
            '/connections',
            headers={"session-id": str(session_id_manager.session_id)},
            json=[
                {
                    'from_type': 'reservoir',
                    'from': 'r1',
                    'to_type': 'plant',
                    'to': 'p1'
                }
            ]
        )
        assert response.status_code == 200
        assert response.json() == None

    # @pytest.mark.order(20)
    def test_get_connections(self, client, session_id_manager):
        response = client.get(
            '/connections',
            headers={"accept": "application/json","Content-Type": "application/json", "session-id": str(session_id_manager.session_id)}
        )
        assert response.status_code == 200
        
        # TODO: connection output is a mess ... SHOP's fault?
        print(json.dumps(response.json(), indent=4))

        # raise Exception("dummy")

        # assert response.json() == [
        #     {
        #         'from_object': {'object_name': 'r1', 'object_type': 'reservoir'},
        #         'relation_direction': 'both',
        #         'relation_type': 'de...: 'both', 'relation_type': 'connection_standard', 'to_object': {'object_name': 'r1', 'object_type': 'reservoir'}

