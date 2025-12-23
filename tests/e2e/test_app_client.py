import base64
import json
import logging
import typing as t
import unittest

import pytest

from arcs_lib_pca.test import ServiceTestCase
from flask.testing import FlaskClient
from faker import Faker

from arcs_lib_pca.utils.settings import Settings
from logging import Logger
from pathlib import Path

class AppClientTestCase(ServiceTestCase):

    logger: Logger
    faker: Faker
    settings: Settings
    client: FlaskClient
    endpoint = '/app_clients'
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
        "Content-Type": "application/json",
        # "X-SERVICE": app.settings.microservice_name,
        # "X-DOMAIN": app.settings.microservice_domain,
        # "Authorization": authorization,
        # "Content-Type": "application/json"
    }

    @ServiceTestCase.loader("../../", "ArcsService")
    def setUp(self):
        name = self.faker.name()
        self.headers['Authorization'] = self.settings.secret_arcs_token #self.env.get("SECRET_ARCS_TOKEN", "")
        self.headers['X-SERVICE'] = name
        self.headers['X-DOMAIN'] = name.replace(' ', '_')

    def create_client(self, name, domain_name):
        payload = {
            "name": domain_name,
            "name_friendly": name,
            "domain": domain_name,
            "description": self.settings.microservice_description,
            "version": self.settings.microservice_version,
            "internal_url": self.settings.microservice_internal_url,
            "external_url": self.settings.microservice_external_url,
            "port": self.settings.microservice_port,
            "namespaces": self.settings.microservice_namespaces
        }
        return self.client.post(f"{self.endpoint}/", headers=self.headers, json=payload)

    def get_image(self):
        with open(Path(__file__).parent.joinpath("./files/icon.png"), 'rb') as file:
            data = file.read()
            file.close()
            return str(base64.b64encode(data))

    def generate_name(self):
        name = self.faker.name()
        domain_name = name.replace(' ', '_').lower()

        return name, domain_name

    def test_create_app_client(self):
        name, domain_name = self.generate_name()

        response = self.create_client(name, domain_name)
        self.log_response(response)
        self.assertEqual(response.status_code, 201)

    def test_get_all_app_client(self):
        response = self.client.get(f"{self.endpoint}/", headers=self.headers)
        self.log_response(response)
        self.assertEqual(response.status_code, 200)

    def test_get_app_client(self):
        name, domain_name = self.generate_name()

        with self.subTest("create_app_client"):
            response = self.create_client(name, domain_name)
            self.log_response(response)
            self.assertEqual(response.status_code, 201)


        with self.subTest("get_app_client"):
            response = self.client.get(f"{self.endpoint}/{domain_name}", headers=self.headers)
            self.log_response(response)
            self.assertEqual(response.status_code, 200)


    def test_delete_app_client(self):
        name, domain_name = self.generate_name()

        with self.subTest("create_app_client"):
            response = self.create_client(name, domain_name)
            self.log_response(response)
            self.assertEqual(response.status_code, 201)

        with self.subTest("get_app_client"):
            response = self.client.get(f"{self.endpoint}/{domain_name}", headers=self.headers)
            self.log_response(response)
            self.assertEqual(response.status_code, 200)

        with self.subTest("delete_app_client"):
            response = self.client.delete(f"{self.endpoint}/{domain_name}", headers=self.headers)
            self.log_response(response)
            self.assertEqual(response.status_code, 200)

        with self.subTest("get_app_client_after_delete"):
            response = self.client.get(f"{self.endpoint}/{domain_name}", headers=self.headers)
            self.log_response(response)
            self.assertEqual(response.status_code, 404)

        with self.subTest("delete_app_client_after_delete"):
            response = self.client.delete(f"{self.endpoint}/{domain_name}", headers=self.headers)
            self.log_response(response)
            self.assertEqual(response.status_code, 404)

    def test_update_app_client(self):
        name, domain_name = self.generate_name()

        with self.subTest("create_app_client"):
            response = self.create_client(name, domain_name)
            self.log_response(response)
            self.assertEqual(response.status_code, 201)

        new_name, new_domain_name = self.generate_name()

        # with self.subTest("update_app_client"):
        #     response = self.client.put(f"{self.endpoint}/{domain_name}", headers=self.headers, json={
        #         "name": new_domain_name,
        #         "name_friendly": new_name,
        #         "description": "new_description",
        #         # "image": {
        #         #     "filename": "icon.png",
        #         #     "mime_type": "image/png",
        #         #     "mime_data": self.get_image(),
        #         #     "path_local": "./images",
        #         #     "path_storage": "./images"
        #         # }
        #     })
        #     self.log_response(response)
        #     self.assertEqual(response.status_code, 200)