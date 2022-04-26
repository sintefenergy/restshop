import pytest
import pandas as pd
# import numpy as np

# # import requests
# from fastapi.testclient import TestClient
# import sys, os
# sys.path.append(os.getcwd())
# from main import app

# client = TestClient(app)

# Set time resolution
class TestBasicRest:
    headers={"Content-Type": "application/json", "session-id": "1"}
    start_time = '2018-02-27T00:00:00Z'
    end_time = '2018-02-28T00:00:00Z'

    # @pytest.mark.order(1)
    def test_set_time_resolution(self, client):
        resp = client.post(
            '/session',
        )
        assert resp.status_code == 200
        # headers["session-id"] = str(resp.json()['session_id'])


        resp = client.put(
            '/time_resolution',
            headers=self.headers,
            json={
                'start_time': self.start_time,
                'end_time': self.end_time,
                'time_unit': 'hour'
            }
        )

        assert resp.status_code == 200

    # pyshop -> starttime = pd.Timestamp('2018-02-27')
    # pyshop -> endtime = pd.Timestamp('2018-02-28')
    # pyshop -> shop.set_time_resolution(starttime=starttime, endtime=endtime, timeunit='hour')

    # Add topology
    # @pytest.mark.order(2)
    def test_add_reservoir(self, client):
        resp = client.put(
            '/model/reservoir?object_name=Reservoir1',
            headers=self.headers,
            json={
                'attributes': {
                    'max_vol': 12,
                    'lrl': 90,
                    'hrl': 100,
                    'vol_head': { # Curve
                        'y_values': [90, 100, 101],
                        'x_values': [0, 12, 14]
                    },
                    'flow_descr': { # Curve 
                        'y_values': [0, 1000],
                        'x_values': [100, 101]
                    }
                }
            }
        )

        assert resp.status_code == 200

    # pyshop -> rsv1 = shop.model.reservoir.add_object('Reservoir1')
    # pyshop -> rsv1.max_vol.set(12)
    # pyshop -> rsv1.lrl.set(90)
    # pyshop -> rsv1.hrl.set(100)
    # pyshop -> rsv1.vol_head.set(pd.Series([90, 100, 101], index=[0, 12, 14], name=0))
    # pyshop -> rsv1.flow_descr.set(pd.Series([0, 1000], index=[100, 101], name=0))

    # @pytest.mark.order(3)
    def test_add_plant(self, client):
        resp = client.put(
            '/model/plant?object_name=Plant1',
            json={
                'attributes': {
                    'outlet_line': 40,
                    'main_loss': [0.0002],
                    'penstock_loss': [0.0001]
                }
            }
        )

        assert resp.status_code == 200

    # plant1 = shop.model.plant.add_object('Plant1')
    # plant1.outlet_line.set(40)
    # plant1.main_loss.set([0.0002])
    # plant1.penstock_loss.set([0.0001])

    # @pytest.mark.order(4)
    def test_add_generator(self, client):
        resp = client.put(
            '/model/generator?object_name=Plant1_G1',
            json={
                'attributes': {
                    'penstock': 1,
                    'p_min': 25,
                    'p_max': 100,
                    'p_nom': 100,
                    'startcost': 500,
                    'gen_eff_curve': { #Curve 
                        'y_values': [95, 98],
                        'x_values': [0, 100]
                    },
                    'turb_eff_curves': { #Dict[float, Curve]
                        '90': { # Curve
                            'y_values': [80, 95, 90],
                            'x_values': [25, 90, 100]
                        },
                        '100': { # Curve
                            'y_values': [82, 98, 92],
                            'x_values': [25, 90, 100]
                        }
                    }
                }
            }
        )

        assert resp.status_code == 200

    # @pytest.mark.order(5)
    def test_connect_generator_and_plant(self, client):
        resp = client.put(
            '/connections',
            json=[
                {
                    'from_type': 'plant',
                    'from': 'Plant1',
                    'to_type': 'generator',
                    'to': 'Plant1_G1'
                }
            ]
        )

        assert resp.status_code == 200

    # p1g1 = shop.model.generator.add_object('Plant1_G1')
    # plant1.connect().generator.Plant1_G1.add()
    # p1g1.penstock.set(1)
    # p1g1.p_min.set(25)
    # p1g1.p_max.set(100)
    # p1g1.p_nom.set(100)
    # p1g1.startcost.set(500)
    # p1g1.gen_eff_curve.set(pd.Series([95, 98], index=[0, 100]))
    # p1g1.turb_eff_curves.set([pd.Series([80, 95, 90], index=[25, 90, 100], name=90),
    #                           pd.Series([82, 98, 92], index=[25, 90, 100], name=100)])

    # @pytest.mark.order(6)
    def test_add_second_reservoir(self, client):
        resp = client.put(
            '/model/reservoir?object_name=Reservoir2',
            json={
                'attributes': {
                    'max_vol': 5,
                    'lrl': 40,
                    'hrl': 50,
                    'vol_head': { # Curve
                        'y_values': [40, 50, 51],
                        'x_values': [0, 5, 6]
                    },
                    'flow_descr': { # Curve 
                        'y_values': [0, 1000],
                        'x_values': [50, 51]
                    }
                }
            }
        )

        assert resp.status_code == 200

    # rsv2 = shop.model.reservoir.add_object('Reservoir2')
    # rsv2.max_vol.set(5)
    # rsv2.lrl.set(40)
    # rsv2.hrl.set(50)
    # rsv2.vol_head.set(pd.Series([40, 50, 51], index=[0, 5, 6]))
    # rsv2.flow_descr.set(pd.Series([0, 1000], index=[50, 51]))

    # @pytest.mark.order(7)
    def test_add_second_plant(self, client):
        resp = client.put(
            '/model/plant?object_name=Plant2',
            json={
                'attributes': {
                    'outlet_line': 0,
                    'main_loss': [0.0002],
                    'penstock_loss': [0.0001]
                }
            }
        )

        assert resp.status_code == 200

    # plant2 = shop.model.plant.add_object('Plant2')
    # plant2.outlet_line.set(0)
    # plant2.main_loss.set([0.0002])
    # plant2.penstock_loss.set([0.0001])

    # @pytest.mark.order(8)
    def test_add_second_generator(self, client):
        resp = client.put(
            '/model/generator?object_name=Plant2_G1',
            json={
                'attributes': {
                    'penstock': 1,
                    'p_min': 25,
                    'p_max': 100,
                    'p_nom': 100,
                    'startcost': 500,
                    'gen_eff_curve': { #Curve 
                        'y_values': [95, 98],
                        'x_values': [0, 100]
                    },
                    'turb_eff_curves': { #Dict[float, Curve]
                        '90': { # Curve
                            'y_values': [80, 95, 90],
                            'x_values': [25, 90, 100]
                        },
                        '100': { # Curve
                            'y_values': [82, 98, 92],
                            'x_values': [25, 90, 100]
                        }
                    }
                }
            }
        )

        assert resp.status_code == 200

    # @pytest.mark.order(9)
    def test_connnect_second_generator_to_plant(self, client):
        resp = client.put(
            '/connections',
            json=[
                {
                    'from_type': 'plant',
                    'from': 'Plant2',
                    'to_type': 'generator',
                    'to': 'Plant2_G1'
                }
            ]
        )

        assert resp.status_code == 200

    # p2g1 = shop.model.generator.add_object('Plant2_G1')
    # plant2.connect().generator.Plant2_G1.add()
    # p2g1.penstock.set(1)
    # p2g1.p_min.set(25)
    # p2g1.p_max.set(100)
    # p2g1.p_nom.set(100)
    # p2g1.startcost.set(500)
    # p2g1.gen_eff_curve.set(pd.Series([95, 98], index=[0, 100]))
    # p2g1.turb_eff_curves.set([pd.Series([80, 95, 90], index=[25, 90, 100], name=90),
    #                           pd.Series([82, 98, 92], index=[25, 90, 100], name=100)])

    # Connect objects

    # @pytest.mark.order(10)
    def test_connect_reservoirs_and_plants(self, client):
        resp = client.put(
            '/connections',
            json=[
                { #Reservoir1 -> Plant1
                    'from_type': 'reservoir',
                    'from': 'Reservoir1',
                    'to_type': 'plant',
                    'to': 'Plant1'
                },
                { # Plant1 -> Reservoir2
                    'from_type': 'plant',
                    'from': 'Plant1',
                    'to_type': 'reservoir',
                    'to': 'Reservoir2'
                },
                { # Reservoir2 -> Plant2
                    'from_type': 'reservoir',
                    'from': 'Reservoir2',
                    'to_type': 'plant',
                    'to': 'Plant2'
                }
            ]
        )

        assert resp.status_code == 200

    # Connect objects (alternative way)

    # Doing this repeatedly causes segmentation fault TODO: investigate this SHOP side bug
    # assert client.put('/connect/reservoir/Reservoir1/plant/Plant1').status_code == 200 # Reservoir1 -> Plant1
    # assert client.put('/connect/plant/Plant1/reservoir/Reservoir2').status_code == 200 # Plant1 -> Reservoir2
    # assert client.put('/connect/reservoir/Reservoir2/plant/Plant2').status_code == 200 # Reservoir2 -> Plant2

    # rsv1.connect().plant.Plant1.add()
    # plant1.connect().reservoir.Reservoir2.add()
    # rsv2.connect().plant.Plant2.add()

    # @pytest.mark.order(11)
    def test_set_resvoir_vw_and_head(self, client):
        resp = client.put(
            '/model/reservoir?object_name=Reservoir1',
            json={
                'attributes': {
                'start_head': 92,
                'energy_value_input': 39.7
                }
            }
        )

        assert resp.status_code == 200

    # @pytest.mark.order(12)
    def test_set_second_reservoir_vw_and_head(self, client):
        resp = client.put(
            '/model/reservoir?object_name=Reservoir2',
            json={
                'attributes': {
                'start_head': 43,
                'energy_value_input': 38.6
                }
            }
        )

        assert resp.status_code == 200

    # rsv1.start_head.set(92)
    # rsv2.start_head.set(43)
    # rsv1.energy_value_input.set(pd.Series([39.7], index=[0]))
    # rsv2.energy_value_input.set(pd.Series([38.6], index=[0]))

    # @pytest.mark.order(13)
    def test_set_market_data(self, client):
        resp = client.put(
            '/model/market?object_name=Day_ahead',
            json={
                'attributes': {
                'sale_price': 39.99,
                'buy_price': 40.01,
                'max_buy': 9999,
                'max_sale': 9999
                }
            }
        )

        assert resp.status_code == 200

    # shop.model.market.add_object('Day_ahead')
    # da = shop.model.market.Day_ahead
    # da.sale_price.set(39.99)
    # da.buy_price.set(40.01)
    # da.max_buy.set(9999)
    # da.max_sale.set(9999)

    # @pytest.mark.order(14)
    def test_set_reservoir_inflow(self, client):
        resp = client.put(
            '/model/reservoir?object_name=Reservoir1',
            json={
                'attributes': {
                'inflow': { # TimeSeries
                        'timestamps': [ self.start_time, (pd.Timestamp(self.start_time) + pd.Timedelta(hours=1)).isoformat() ],
                        'values': [[101, 50]]
                }
                }
            }
        )

        assert resp.status_code == 200

    # rsv1.inflow.set(pd.DataFrame([101, 50], index=[starttime, starttime + pd.Timedelta(hours=1)]))

    # @pytest.mark.order(15)
    def test_start_sim_inc(self, client):
        resp = client.post(
            '/simulation/start_sim',
            json={
                'options': [],
                'values': ['3']
            }
        )

        assert resp.status_code == 200
    
    def test_set_code(self, client):
        resp = client.post(
            '/simulation/set_code',
            json={
                'options': ['incremental'],
                'values': []
            }
        )

        assert resp.status_code == 200
    
    def test_start_sim_full(self, client):
        resp = client.post(
            '/simulation/start_sim',
            json={
                'options': [],
                'values': ['3']
            }
        )

        assert resp.status_code == 200

    # shop.start_sim([], ['3'])
    # shop.set_code(['incremental'], [])
    # shop.start_sim([], ['3'])

    # @pytest.mark.order(16)
    def test_get_price(self, client):
        resp = client.get('/model/market/?object_name=Day_ahead')
        assert resp.status_code == 200

    # ax = shop.model.market.Day_ahead.sale_price.get().plot(legend='Price', secondary_y=True)

    # @pytest.mark.order(17)
    def test_get_plant_attributes(self, client):
        resp = client.get('/model/plant/?object_name=Plant1')
        assert resp.status_code == 200
        plant_1 = resp.json()

        resp = client.get('/model/plant/?object_name=Plant2')
        assert resp.status_code == 200
        plant_2 = resp.json()

    # shop.model.plant.Plant1.production.get().plot(legend='Plant 1')
    # shop.model.plant.Plant2.production.get().plot(legend='Plant 2')
    # ax.set_ylabel('Price [NOK]')
    # plt.show()

    # @pytest.mark.order(18)
    def test_get_reservoir_attributes(self, client):
        resp = client.get('/model/reservoir/?object_name=Reservoir1')
        assert resp.status_code == 200
        reservoir_1 = resp.json()

        resp = client.get('/model/reservoir/?object_name=Reservoir2')
        assert resp.status_code == 200
        reservoir_2 = resp.json()