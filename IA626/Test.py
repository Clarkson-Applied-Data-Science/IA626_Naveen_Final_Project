import unittest
import requests

class APITestCase(unittest.TestCase):
    BASE_URL = 'http://127.0.0.1:5000'

    def test_upload_csv(self):
        url = f'{self.BASE_URL}/upload/deaths'
        files = {'file': ('C:/Users/Asus/OneDrive/Desktop/web development/Project/deaths_clean_df.csv', open('deaths_clean_df.csv', 'rb'), 'text/csv')}
        response = requests.post(url, files=files)
        self.assertEqual(response.status_code, 302)

    def test_create_data(self):
        url = f'{self.BASE_URL}/api/data'
        data = {
            'country': 'Afghanistan',
            'date': '2022-03-25',
            'accumulated_confirmed': 100,
            'accumulated_deaths': 5,
            'accumulated_recovered': 95
        }
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 201)

    def test_read_data(self):
        data_id = 1
        url = f'{self.BASE_URL}/api/data/{data_id}'
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('country', response.json())

    def test_update_data(self):
        data_id = 1
        url = f'{self.BASE_URL}/api/data/{data_id}'
        data = {
            'accumulated_confirmed': 120,
            'accumulated_deaths': 10,
            'accumulated_recovered': 110
        }
        response = requests.put(url, json=data)
        self.assertEqual(response.status_code, 200)

    def test_delete_data(self):
        data_id = 2
        url = f'{self.BASE_URL}/api/data/{data_id}'
        response = requests.delete(url)
        self.assertEqual(response.status_code, 200)

    def test_get_country_data(self):
        url = f'{self.BASE_URL}/api/stats?country=TestLand&start_date=2022-01-01&end_date=2022-12-31'
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_total_counts(self):
        url = f'{self.BASE_URL}/api/total_counts'
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()

