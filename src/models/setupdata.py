"""setupdata.py"""
import os
import json
from typing import List
from models import ChecklistModel, VulnerabilityModel
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

class SetupData: # pylint: disable=R0903
    """SetupData."""

    def get_owasp_wstg_checklist(self) -> list[ChecklistModel]:
        """Get OWASP WSTG Checklist data."""
        data: list[ChecklistModel] = []
        CHECKLIST_NAME = 'OWASP Web Security Testing Guide' # pylint: disable=C0103
        CHECKLIST_VERSION = 4.2 # pylint: disable=C0103

        # USEFUL_TOOLS based on list from:
        # https://github.com/tanprathan/OWASP-Testing-Checklist
        USEFUL_TOOLS: dict[str, str] = { # pylint: disable=C0103
            'WSTG-INFO-01': 'search engine;shodan;recon-ng',
            'WSTG-INFO-02': 'nikto;search engine;wappalyzer',
            'WSTG-INFO-03': 'curl;proxy;web browser',
            'WSTG-INFO-04': 'dnsrecon;nmap',
            'WSTG-INFO-05': 'curl;proxy;web browser',
            'WSTG-INFO-06': 'owasp attack surface detector;proxy',
            'WSTG-INFO-07': 'proxy',
            'WSTG-INFO-08': 'cmsmap;wappalyzer;whatweb',
            'WSTG-INFO-09': 'cmsmap;wappalyzer;whatweb',
            'WSTG-INFO-10': 'nmap;proxy;wafw00f'
        }

        # WSTG - v4.2
        # https://github.com/OWASP/wstg/releases/tag/v4.2
        # https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/
        with open(f'{BASE_PATH}/owasp_wstg_checklist.json', mode='r', encoding='utf-8') as f:
            raw_data = json.load(f)

        item_no = 1
        category_order = 1
        for category in raw_data['categories']:
            for test in raw_data['categories'][category]['tests']:
                if test['name'] == 'Testing for Buffer Overflow':
                    continue
                checklist_item = ChecklistModel()
                checklist_item.id = item_no
                checklist_item.name = CHECKLIST_NAME
                checklist_item.checklist_version = CHECKLIST_VERSION
                checklist_item.category = category
                checklist_item.category_id = raw_data['categories'][category]['id']
                checklist_item.category_order = category_order
                checklist_item.item_name = test['name']
                checklist_item.item_id = test['id']
                checklist_item.link = test['reference']
                checklist_item.objectives = ';'.join(test['objectives'])
                checklist_item.useful_tools = USEFUL_TOOLS.get(checklist_item.item_id, None)
                data.append(checklist_item)
                item_no += 1
            category_order += 1

        return data

    def get_vulnerabilities(self):
        """Get vulnerabilities data."""
        with open(f'{BASE_PATH}/vulnerabilities.json', mode='r', encoding='utf-8') as f:
            raw_data = json.load(f)

        records: List[VulnerabilityModel] = []

        for record in raw_data:
            vulnerability: VulnerabilityModel = VulnerabilityModel(
                vuln_category_id = record['vuln_category_id'],
                parent_category_id = record['parent_category_id'],
                category_name = record['category_name'],
                category_acronym = record['category_acronym'],
                cwe_id = record['cwe_id'],
                cwe_name = record['cwe_name'],
                cwe_link = record['cwe_link'],
                capec_id = record['capec_id'],
                capec_name = record['capec_name'],
                capec_link = record['capec_link'],
                kev_link = record['kev_link'],
                references = record['references'],
                cheatsheets = record['cheatsheets'],
                tools = record['tools'],
                payload_lists = record['payload_lists'],
                tests = record['tests']
            )
            records.append(vulnerability)

        return records
