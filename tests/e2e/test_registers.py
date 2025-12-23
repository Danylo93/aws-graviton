# import unittest
#
# import pytest
#
# from arcs_lib_pca.test import ServiceTestCase
# from flask.testing import FlaskClient
#
# class RegistersTestCase(ServiceTestCase):
#
#     client: FlaskClient
#     endpoint = '/registers'
#     headers = {
#         "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
#         "Content-Type": "application/json"
#     }
#
#     @ServiceTestCase.loader("../../", "ArcsService")
#     def setUp(self):
#         pass
#
#     def test_register_accounts_user(self):
#         with self.subTest(msg="without_body"):
#             response = self.client.post(
#                 path=f"{self.endpoint}/",
#                 headers=self.headers
#             )
#             self.assertEqual(response.status_code, 400)
#             self.assertEqual(['email', 'person'], self.extract_fields_errors(response.text))
#
#         with self.subTest(msg="empty_email"):
#             response = self.client.post(
#                 path=f"{self.endpoint}/",
#                 headers=self.headers,
#                 json={
#                     "email": ""
#                 }
#             )
#             self.assertEqual(response.status_code, 400)
#             self.assertEqual(['email', 'person'], self.extract_fields_errors(response.text))
#
#         with self.subTest(msg="invalid_email"):
#             response = self.client.post(
#                 path=f"{self.endpoint}/",
#                 headers=self.headers,
#                 json={
#                     "email": "a_com"
#                 }
#             )
#             self.assertEqual(response.status_code, 400)
#             self.assertEqual(['email', 'person'], self.extract_fields_errors(response.text))
#
#         with self.subTest(msg="without_person"):
#             response = self.client.post(
#                 path=f"{self.endpoint}/",
#                 headers=self.headers,
#                 json={
#                     "email": "a@a.com"
#                 }
#             )
#             self.assertEqual(response.status_code, 400)
#             self.assertEqual(['person'], self.extract_fields_errors(response.text))
#
#         with self.subTest(msg="invalid_person"):
#             response = self.client.post(
#                 path=f"{self.endpoint}/",
#                 headers=self.headers,
#                 json={
#                     "email": "a@a.com",
#                     "person": {}
#                 }
#             )
#             self.assertEqual(response.status_code, 400)
#             self.assertEqual(['person', 'full_name'], self.extract_fields_errors(response.text))
#
#         with self.subTest(msg="empty_name"):
#             response = self.client.post(
#                 path=f"{self.endpoint}/",
#                 headers=self.headers,
#                 json={
#                     "email": "a@a.com",
#                     "person": {
#                         'full_name': ''
#                     }
#                 }
#             )
#             self.assertEqual(response.status_code, 400)
#             self.assertEqual(['person', 'full_name'], self.extract_fields_errors(response.text))
#
#         with self.subTest(msg="invalid_name"):
#             response = self.client.post(
#                 path=f"{self.endpoint}/",
#                 headers=self.headers,
#                 json={
#                     "email": "a@a.com",
#                     "person": {
#                         'full_name': 'Lucas'
#                     }
#                 }
#             )
#             self.assertEqual(response.status_code, 400)
#             self.assertEqual(['person', 'full_name'], self.extract_fields_errors(response.text))
#
#         with self.subTest(msg="valid_payload"):
#             response = self.client.post(
#                 path=f"{self.endpoint}/",
#                 headers=self.headers,
#                 json={
#                     "email": "a@a.com",
#                     "person": {
#                         'full_name': 'Lucas'
#                     }
#                 }
#             )
#             print(response.text)
#             self.assertEqual(response.status_code, 400)
#             self.assertEqual(['person', 'full_name'], self.extract_fields_errors(response.text))