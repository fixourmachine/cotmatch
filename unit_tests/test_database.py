"""
CotMatch — Neonatal Unit Database Integrity Tests
==================================================
Run from the project root:
    python3 tests/test_database.py

Tests cover:
  - Schema completeness for every unit
  - No duplicated unit names
  - UK-bounds geocoding validation
  - Clinical data plausibility
  - No forbidden placeholder strings
  - Required known units present with correct data
  - Capability consistency vs BAPM level
  - Phone number format validity
  - ODN/transport team assignments
"""

import json
import re
import sys
import os
import unittest

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'uk_neonatal_units.json')

with open(DB_PATH, 'r', encoding='utf-8') as f:
    DATA = json.load(f)

# ── Helpers ────────────────────────────────────────────────────────────────────

def unit(name_fragment):
    """Return first unit whose name contains the fragment (case-insensitive)."""
    matches = [u for u in DATA if name_fragment.lower() in u['unit_name'].lower()
               or name_fragment.lower() in u.get('unit_name_full', '').lower()]
    return matches[0] if matches else None


# ── Test Classes ───────────────────────────────────────────────────────────────

class TestSchemaCompleteness(unittest.TestCase):
    """Every unit must have all required top-level fields with correct types."""

    REQUIRED_FIELDS = {
        'unit_name': str,
        'unit_name_full': str,
        'unit_postcode': str,
        'address': str,
        'trust': str,
        'network_odn': str,
        'regional_transport_team': str,
        'telephone_numbers': list,
        'latitude': float,
        'longitude': float,
        'accepts_weight_from': (int, float),
        'accepts_gestation_from': (int, float),
        'minimum_level_of_care': (int, float),
        'nursing_capabilities': dict,
        'advanced_facilities': dict,
        'specialties': dict,
    }

    NURSING_KEYS = [
        'cpap_hhfnc', 'hourly_ngt_feeds', 'njt_care', 'continuous_pump_feeds',
        'parenteral_nutrition', 'long_line_picc', 'broviac_hickman',
        'ventricular_taps', 'convulsion_mgmt', 'stoma_care',
        'tracheostomy_care', 'palliative_care',
    ]

    ADVANCED_KEYS = [
        'ino', 'respiratory_ecmo', 'active_cooling', 'laser_rop', 'on_site_picu',
    ]

    SPECIALTY_KEYS = [
        'on_site_gen_surgery', 'on_site_neurosurgery', 'on_site_cardiology',
        'paediatric_ent', 'paed_anaesthetic_support', 'paed_resp_ltv',
    ]

    def test_required_top_level_fields_present(self):
        for u in DATA:
            for field, expected_type in self.REQUIRED_FIELDS.items():
                with self.subTest(unit=u['unit_name'], field=field):
                    self.assertIn(field, u, f"Missing field '{field}'")
                    self.assertIsInstance(u[field], expected_type,
                                         f"Wrong type for '{field}'")

    def test_nursing_capabilities_keys_complete(self):
        for u in DATA:
            nc = u.get('nursing_capabilities', {})
            for key in self.NURSING_KEYS:
                with self.subTest(unit=u['unit_name'], key=key):
                    self.assertIn(key, nc, f"Missing nursing capability: {key}")
                    self.assertIsInstance(nc[key], bool)

    def test_advanced_facilities_keys_complete(self):
        for u in DATA:
            af = u.get('advanced_facilities', {})
            for key in self.ADVANCED_KEYS:
                with self.subTest(unit=u['unit_name'], key=key):
                    self.assertIn(key, af, f"Missing advanced facility: {key}")
                    self.assertIsInstance(af[key], bool)

    def test_specialties_keys_complete(self):
        for u in DATA:
            sp = u.get('specialties', {})
            for key in self.SPECIALTY_KEYS:
                with self.subTest(unit=u['unit_name'], key=key):
                    self.assertIn(key, sp, f"Missing specialty: {key}")
                    self.assertIsInstance(sp[key], bool)


class TestNoDuplicates(unittest.TestCase):
    """No two units should share identical names or identical coordinates."""

    def test_no_duplicate_unit_names(self):
        names = [u['unit_name'] for u in DATA]
        seen = {}
        for n in names:
            seen[n] = seen.get(n, 0) + 1
        dups = {k: v for k, v in seen.items() if v > 1}
        self.assertFalse(dups, f"Duplicate unit names found: {dups}")

    def test_no_duplicate_coordinates(self):
        coords = [(u['latitude'], u['longitude']) for u in DATA]
        seen = {}
        for c in coords:
            seen[c] = seen.get(c, 0) + 1
        dups = {str(k): v for k, v in seen.items() if v > 1}
        self.assertFalse(dups, f"Duplicate coordinates (ghost entries?): {dups}")


class TestGeocoding(unittest.TestCase):
    """All coordinates must fall within approximate UK bounding box."""

    UK_LAT = (49.5, 61.0)   # Isles of Scilly → Shetland
    UK_LON = (-8.2, 2.0)    # West Ireland coast → East Anglia

    def test_all_coordinates_within_uk(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                lat, lon = u['latitude'], u['longitude']
                self.assertGreaterEqual(lat, self.UK_LAT[0],
                                        f"Latitude {lat} too far south")
                self.assertLessEqual(lat, self.UK_LAT[1],
                                     f"Latitude {lat} too far north")
                self.assertGreaterEqual(lon, self.UK_LON[0],
                                        f"Longitude {lon} too far west")
                self.assertLessEqual(lon, self.UK_LON[1],
                                     f"Longitude {lon} too far east")

    def test_no_placeholder_zero_zero_coordinates(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                self.assertFalse(u['latitude'] == 0 and u['longitude'] == 0,
                                 "Unit has placeholder 0,0 coordinates")

    def test_no_round_number_fallback_coordinates(self):
        """Catch lazy fallback geocoding e.g. 53.0, -2.0"""
        for u in DATA:
            lat, lon = u['latitude'], u['longitude']
            with self.subTest(unit=u['unit_name']):
                is_suspicious = (lat == round(lat, 0) and lon == round(lon, 0))
                self.assertFalse(is_suspicious,
                                 f"Suspiciously round coordinates: {lat}, {lon}")


class TestClinicalPlausibility(unittest.TestCase):
    """Clinical data values must be within medically sensible ranges."""

    def test_level_of_care_is_1_2_or_3(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                level = int(str(u['minimum_level_of_care']).replace('L', ''))
                self.assertIn(level, [1, 2, 3],
                              f"Invalid level: {u['minimum_level_of_care']}")

    def test_gestation_limits_are_plausible(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                gest = u['accepts_gestation_from']
                # 0 means no limit; otherwise must be between 22 and 37 weeks
                if gest > 0:
                    self.assertGreaterEqual(gest, 22,
                                            f"Gestation {gest}w seems too early")
                    self.assertLessEqual(gest, 37,
                                         f"Gestation {gest}w seems too late for a neonatal unit")

    def test_weight_limits_are_plausible(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                wt = u['accepts_weight_from']
                # 0 means no limit; otherwise must be between 300g and 2500g
                if wt > 0:
                    self.assertGreaterEqual(wt, 300,
                                            f"Weight {wt}g seems implausibly low")
                    self.assertLessEqual(wt, 2500,
                                         f"Weight {wt}g seems too high for a minimum")

    def test_level1_units_do_not_claim_ecmo(self):
        for u in DATA:
            level = int(str(u['minimum_level_of_care']).replace('L', ''))
            if level == 1:
                with self.subTest(unit=u['unit_name']):
                    self.assertFalse(
                        u['advanced_facilities'].get('respiratory_ecmo', False),
                        "L1 SCBU claiming ECMO capability — likely data error"
                    )

    def test_level1_units_do_not_claim_ino(self):
        for u in DATA:
            level = int(str(u['minimum_level_of_care']).replace('L', ''))
            if level == 1:
                with self.subTest(unit=u['unit_name']):
                    self.assertFalse(
                        u['advanced_facilities'].get('ino', False),
                        "L1 SCBU claiming iNO capability — likely data error"
                    )


class TestNoPlaceholderStrings(unittest.TestCase):
    """No unit should contain forbidden placeholder or default strings."""

    FORBIDDEN = [
        'Unknown ODN', 'Unknown Transport', 'Unlisted',
        'See ODN Directory', 'Unknown', 'TODO', 'N/A', 'TBC',
    ]

    def test_no_forbidden_strings_in_odn(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                for f in self.FORBIDDEN:
                    self.assertNotEqual(u.get('network_odn', ''), f,
                                        f"ODN is '{f}'")

    def test_no_forbidden_strings_in_transport(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                for f in self.FORBIDDEN:
                    self.assertNotEqual(u.get('regional_transport_team', ''), f,
                                        f"Transport team is '{f}'")

    def test_phone_numbers_not_empty(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                phones = u.get('telephone_numbers', [])
                self.assertTrue(len(phones) > 0,
                                "telephone_numbers array is empty")
                self.assertNotEqual(phones[0].strip(), '',
                                    "First telephone number is blank")


class TestPhoneNumberFormat(unittest.TestCase):
    """Phone numbers should follow recognisable UK patterns."""

    # Matches: 01xxx xxxxxx, 02x xxxx xxxx, 03xx xxx xxxx, 07xxx xxxxxx, 0800 xxx xxx
    UK_PHONE_RE = re.compile(r'^0[\d\s\-]{9,14}$')

    def test_phone_numbers_look_like_uk_numbers(self):
        for u in DATA:
            phones = u.get('telephone_numbers', [])
            for phone in phones:
                with self.subTest(unit=u['unit_name'], phone=phone):
                    stripped = phone.replace(' ', '').replace('-', '')
                    self.assertTrue(
                        stripped.startswith('0') and stripped.isdigit() and 10 <= len(stripped) <= 11,
                        f"Suspicious phone number: '{phone}'"
                    )


class TestKnownUnits(unittest.TestCase):
    """Spot-check that specific well-known units exist with correct critical data."""

    def test_gosh_exists_and_is_level3(self):
        u = unit("Great Ormond Street")
        self.assertIsNotNone(u, "GOSH not found in database")
        level = int(str(u['minimum_level_of_care']).replace('L', ''))
        self.assertEqual(level, 3, f"GOSH should be Level 3, got {level}")

    def test_gosh_has_neurosurgery(self):
        u = unit("Great Ormond Street")
        self.assertTrue(u['specialties'].get('on_site_neurosurgery', False),
                        "GOSH should have on-site neurosurgery")

    def test_liverpool_womens_exists(self):
        u = unit("Liverpool Women")
        self.assertIsNotNone(u, "Liverpool Women's Hospital not found")

    def test_edinburgh_royal_infirmary_is_scotland_network(self):
        u = unit("Edinburgh Royal")
        self.assertIsNotNone(u, "Edinburgh Royal Infirmary not found")
        self.assertEqual(u['network_odn'], 'Scotland')

    def test_edinburgh_transport_is_scotstar(self):
        u = unit("Edinburgh Royal")
        self.assertEqual(u['regional_transport_team'], 'ScotSTAR')

    def test_countess_chester_is_level1(self):
        u = unit("Countess Chester")
        self.assertIsNotNone(u, "Countess Chester not found")
        level = int(str(u['minimum_level_of_care']).replace('L', ''))
        self.assertEqual(level, 1, f"Countess Chester should be Level 1, got {level}")

    def test_countess_chester_gestation_limit(self):
        u = unit("Countess Chester")
        self.assertEqual(u['accepts_gestation_from'], 32,
                         "Countess Chester should have 32w gestation limit")

    def test_royal_free_is_removed(self):
        u = unit("Royal Free")
        self.assertIsNone(u, "Royal Free should have been removed (closed March 2025)")

    def test_horton_general_is_removed(self):
        u = unit("Horton General")
        self.assertIsNone(u, "Horton General should have been removed (permanently closed)")

    def test_yeovil_is_removed(self):
        u = unit("Yeovil")
        self.assertIsNone(u, "Yeovil District Hospital should have been removed (closed May 2025)")

    def test_poole_hospital_is_removed(self):
        matches = [u for u in DATA if 'Poole Hospital NHS Foundation Trust' == u['unit_name']]
        self.assertEqual(len(matches), 0,
                         "Old Poole Hospital entry should have been replaced by Royal Bournemouth")

    def test_royal_bournemouth_exists(self):
        u = unit("Royal Bournemouth")
        self.assertIsNotNone(u, "Royal Bournemouth Hospital not found (should replace Poole)")

    def test_queen_elizabeth_woolwich_searchable(self):
        """Full name must expand so 'Queen Elizabeth Woolwich' finds 'Q. Elizabeth Hosp'"""
        matches = [u for u in DATA
                   if 'queen elizabeth' in u.get('unit_name_full', '').lower()
                   and 'woolwich' in (u.get('address', '') + u.get('unit_postcode', '')).lower()]
        self.assertTrue(len(matches) > 0,
                        "Queen Elizabeth Hospital (Woolwich) not findable via full name search")

    def test_wishaw_is_level2(self):
        u = unit("Wishaw")
        self.assertIsNotNone(u, "University Hospital Wishaw not found")
        level = int(str(u['minimum_level_of_care']).replace('L', ''))
        self.assertEqual(level, 2, f"Wishaw should be Level 2 (Best Start downgrade), got {level}")

    def test_fife_victoria_not_duplicated(self):
        matches = [u for u in DATA if 'Fife Victoria' in u['unit_name']]
        self.assertEqual(len(matches), 1,
                         f"Fife Victoria Hospital is duplicated ({len(matches)} entries)")

    def test_no_blackpool_assigned_to_scotland(self):
        u = unit("Blackpool Victoria")
        self.assertIsNotNone(u, "Blackpool Victoria Hospital not found")
        self.assertNotEqual(u['network_odn'], 'Scotland',
                            "Blackpool Victoria incorrectly assigned to Scotland network")

    def test_northumbria_correct_network(self):
        u = unit("Northumbria Specialist")
        self.assertIsNotNone(u, "Northumbria Specialist Emergency Care Hospital not found")
        self.assertEqual(u['network_odn'], 'Northern',
                         f"Northumbria should be Northern network, got {u['network_odn']}")

    def test_northumbria_correct_trust(self):
        u = unit("Northumbria Specialist")
        self.assertIn("Northumbria Healthcare", u['trust'],
                      f"Northumbria trust incorrect: {u['trust']}")


class TestDatabaseCoverage(unittest.TestCase):
    """Broad coverage checks."""

    def test_minimum_unit_count(self):
        self.assertGreaterEqual(len(DATA), 180,
                                f"Expected at least 180 units, got {len(DATA)}")

    def test_all_four_nations_represented(self):
        odns = set(u['network_odn'] for u in DATA)
        self.assertIn('Scotland', odns, "No Scottish units found")
        self.assertIn('Wales', odns, "No Welsh units found")
        self.assertIn('Northern Ireland', odns, "No Northern Irish units found")
        # England has many networks
        english_networks = {'London', 'North West', 'Northern', 'Yorkshire & Humber',
                            'East Midlands', 'West Midlands', 'East of England',
                            'Thames Valley & Wessex', 'Kent, Surrey & Sussex', 'South West'}
        found = english_networks & odns
        self.assertTrue(len(found) >= 8,
                        f"Expected 8+ English networks, found: {found}")

    def test_all_units_have_postcodes(self):
        missing = [u['unit_name'] for u in DATA
                   if not u.get('unit_postcode', '').strip()]
        self.assertFalse(missing, f"Units with missing postcodes: {missing}")

    def test_postcodes_look_valid(self):
        # Basic UK postcode pattern (not exhaustive)
        pc_re = re.compile(r'^[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}$', re.IGNORECASE)
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                pc = u.get('unit_postcode', '').strip()
                self.assertTrue(pc_re.match(pc), f"Suspicious postcode: '{pc}'")

    def test_trust_names_end_with_trust(self):
        trust_suffixes = ('Trust', 'Board', 'Authority')
        for u in DATA:
            trust = u.get('trust', '')
            with self.subTest(unit=u['unit_name']):
                ends_ok = any(trust.strip().endswith(s) for s in trust_suffixes)
                self.assertTrue(ends_ok,
                                f"Trust name doesn't end with Trust/Board/Authority: '{trust}'")

    def test_full_names_longer_than_display_names(self):
        """Full names should generally be equal or longer (expansions always add characters)."""
        for u in DATA:
            name = u.get('unit_name', '')
            full = u.get('unit_name_full', '')
            with self.subTest(unit=name):
                self.assertGreaterEqual(len(full), len(name),
                                        f"Full name '{full}' shorter than display name '{name}'")


# ── Extended Test Classes ──────────────────────────────────────────────────────

class TestTransportConsistency(unittest.TestCase):
    """Transport teams must be geographically consistent with their ODN."""

    def test_scottish_units_use_scotstar(self):
        for u in DATA:
            if u.get('network_odn') == 'Scotland':
                with self.subTest(unit=u['unit_name']):
                    self.assertEqual(u['regional_transport_team'], 'ScotSTAR',
                        f"Scottish unit '{u['unit_name']}' uses {u['regional_transport_team']} not ScotSTAR")

    def test_welsh_units_use_chants(self):
        for u in DATA:
            if u.get('network_odn') == 'Wales':
                with self.subTest(unit=u['unit_name']):
                    self.assertEqual(u['regional_transport_team'], 'CHANTS',
                        f"Welsh unit '{u['unit_name']}' uses {u['regional_transport_team']} not CHANTS")

    def test_northern_ireland_units_use_nistar(self):
        for u in DATA:
            if u.get('network_odn') == 'Northern Ireland':
                with self.subTest(unit=u['unit_name']):
                    self.assertEqual(u['regional_transport_team'], 'NISTAR',
                        f"NI unit '{u['unit_name']}' uses {u['regional_transport_team']} not NISTAR")

    def test_no_english_unit_uses_scotstar(self):
        for u in DATA:
            if u.get('regional_transport_team') == 'ScotSTAR':
                with self.subTest(unit=u['unit_name']):
                    is_scotland = (u['network_odn'] == 'Scotland' or u['latitude'] > 54.6)
                    self.assertTrue(is_scotland,
                        f"'{u['unit_name']}' uses ScotSTAR but appears to be in England")

    def test_no_english_unit_uses_nistar(self):
        for u in DATA:
            if u.get('regional_transport_team') == 'NISTAR':
                with self.subTest(unit=u['unit_name']):
                    self.assertEqual(u['network_odn'], 'Northern Ireland',
                        f"'{u['unit_name']}' uses NISTAR but not in NI ODN")

    def test_transport_team_field_not_blank(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                self.assertTrue(len(u.get('regional_transport_team', '').strip()) > 0,
                    "Transport team is blank")


class TestGeospatialClustering(unittest.TestCase):
    """Units should be geographically near their claimed network region."""

    def _dist(self, lat1, lon1, lat2, lon2):
        import math
        R = 3958.8
        dLat = (lat2 - lat1) * math.pi / 180
        dLon = (lon2 - lon1) * math.pi / 180
        a = math.sin(dLat/2)**2 + math.cos(lat1*math.pi/180)*math.cos(lat2*math.pi/180)*math.sin(dLon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def test_london_units_are_near_london(self):
        for u in [u for u in DATA if u.get('network_odn') == 'London']:
            with self.subTest(unit=u['unit_name']):
                dist = self._dist(51.5074, -0.1278, u['latitude'], u['longitude'])
                self.assertLessEqual(dist, 45,
                    f"'{u['unit_name']}' is {dist:.1f}mi from London — too far for London ODN")

    def test_scottish_units_are_in_scotland(self):
        for u in [u for u in DATA if u.get('network_odn') == 'Scotland']:
            with self.subTest(unit=u['unit_name']):
                self.assertGreater(u['latitude'], 54.5,
                    f"'{u['unit_name']}' lat {u['latitude']} is below Scottish border")

    def test_northern_ireland_units_longitude(self):
        for u in [u for u in DATA if u.get('network_odn') == 'Northern Ireland']:
            with self.subTest(unit=u['unit_name']):
                self.assertLess(u['longitude'], -5.0,
                    f"'{u['unit_name']}' lon {u['longitude']} doesn't look like NI")

    def test_south_west_units_latitude(self):
        for u in [u for u in DATA if u.get('network_odn') == 'South West']:
            with self.subTest(unit=u['unit_name']):
                self.assertLess(u['latitude'], 52.5,
                    f"'{u['unit_name']}' lat {u['latitude']} too far north for South West")

    def test_north_west_units_latitude(self):
        for u in [u for u in DATA if u.get('network_odn') == 'North West']:
            with self.subTest(unit=u['unit_name']):
                self.assertGreater(u['latitude'], 52.5,
                    f"'{u['unit_name']}' lat {u['latitude']} too far south for North West")


class TestCapabilityLogicConsistency(unittest.TestCase):
    """Capability flags must be internally clinically consistent."""

    def _level(self, u):
        return int(str(u['minimum_level_of_care']).replace('L', ''))

    def test_ecmo_units_are_level3(self):
        for u in DATA:
            if u['advanced_facilities'].get('respiratory_ecmo', False):
                with self.subTest(unit=u['unit_name']):
                    self.assertEqual(self._level(u), 3,
                        f"'{u['unit_name']}' has ECMO but is Level {self._level(u)}")

    def test_active_cooling_not_at_level1(self):
        for u in DATA:
            if u['advanced_facilities'].get('active_cooling', False):
                with self.subTest(unit=u['unit_name']):
                    self.assertGreaterEqual(self._level(u), 2,
                        f"'{u['unit_name']}' has active cooling but is Level {self._level(u)}")

    def test_l3_units_have_cpap(self):
        for u in DATA:
            if self._level(u) == 3:
                with self.subTest(unit=u['unit_name']):
                    self.assertTrue(u['nursing_capabilities'].get('cpap_hhfnc', False),
                        f"Level 3 NICU '{u['unit_name']}' lacks CPAP")

    def test_l3_units_have_parenteral_nutrition(self):
        for u in DATA:
            if self._level(u) == 3:
                with self.subTest(unit=u['unit_name']):
                    self.assertTrue(u['nursing_capabilities'].get('parenteral_nutrition', False),
                        f"Level 3 NICU '{u['unit_name']}' lacks PN")

    def test_neurosurgery_implies_level3(self):
        for u in DATA:
            if u['specialties'].get('on_site_neurosurgery', False):
                with self.subTest(unit=u['unit_name']):
                    self.assertEqual(self._level(u), 3,
                        f"'{u['unit_name']}' claims neurosurgery but is Level {self._level(u)}")

    def test_on_site_cardiology_implies_level3(self):
        for u in DATA:
            if u['specialties'].get('on_site_cardiology', False):
                with self.subTest(unit=u['unit_name']):
                    self.assertEqual(self._level(u), 3,
                        f"'{u['unit_name']}' claims cardiology but is Level {self._level(u)}")

    def test_average_l3_weight_limit_lower_than_l2(self):
        l3 = [u['accepts_weight_from'] for u in DATA
              if int(str(u['minimum_level_of_care']).replace('L','')) == 3 and u['accepts_weight_from'] > 0]
        l2 = [u['accepts_weight_from'] for u in DATA
              if int(str(u['minimum_level_of_care']).replace('L','')) == 2 and u['accepts_weight_from'] > 0]
        if l3 and l2:
            self.assertLessEqual(sum(l3)/len(l3), sum(l2)/len(l2),
                f"Avg L3 weight limit ({sum(l3)/len(l3):.0f}g) should be <= L2 ({sum(l2)/len(l2):.0f}g)")


class TestAddressQuality(unittest.TestCase):
    """Address fields should contain useful, structured location data."""

    def test_addresses_are_not_empty(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                self.assertTrue(len(u.get('address', '').strip()) > 3,
                    "Address is empty or too short")

    def test_addresses_not_just_region_names(self):
        bad = re.compile(r'^(city of|county of|borough of|district of|region of)\s+\w+$', re.I)
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                self.assertFalse(bad.match(u.get('address', '').strip()),
                    f"Address too vague: '{u['address']}'")



    def test_address_not_same_as_unit_name(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                self.assertNotEqual(u.get('unit_name','').strip().lower(),
                    u.get('address','').strip().lower(),
                    "Address is identical to unit name")


class TestPhoneUniqueness(unittest.TestCase):
    """Same phone should not appear across 3+ unrelated hospitals."""

    def test_no_phone_shared_across_3_plus_units(self):
        phone_count = {}
        for u in DATA:
            for phone in u.get('telephone_numbers', []):
                stripped = phone.replace(' ', '').replace('-', '')
                if stripped.startswith('0') and stripped.isdigit():
                    phone_count[stripped] = phone_count.get(stripped, 0) + 1
        overused = {p: c for p, c in phone_count.items() if c >= 3}
        self.assertFalse(overused,
            f"Phone numbers in 3+ units (possible copy-paste): {overused}")


class TestRegionalCityPresence(unittest.TestCase):
    """Key UK cities must have at least one neonatal unit in the database."""

    CITIES = [
        ('London',      'network_odn', 5),
        ('Manchester',  'address',     1),
        ('Leeds',       'address',     1),
        ('Bristol',     'address',     1),
        ('Sheffield',   'address',     1),
        ('Liverpool',   'address',     1),
        ('Birmingham',  'address',     1),
        ('Edinburgh',   'address',     1),
        ('Glasgow',     'address',     1),
        ('Cardiff',     'address',     1),
        ('Belfast',     'address',     1),
        ('Newcastle',   'address',     1),
        ('Nottingham',  'address',     1),
        ('Leicester',   'address',     1),
    ]

    def test_major_cities_have_units(self):
        for city, field, min_count in self.CITIES:
            with self.subTest(city=city):
                matches = [u for u in DATA
                           if city.lower() in (u.get(field,'') + ' ' +
                              u.get('unit_name','') + ' ' +
                              u.get('unit_name_full','') + ' ' +
                              u.get('address','')).lower()]
                self.assertGreaterEqual(len(matches), min_count,
                    f"{city} not found in database (expected {min_count}+ units)")


class TestSpotCheckPhoneNumbers(unittest.TestCase):
    """Verify specific known-correct phone numbers."""

    def _phone(self, frag):
        u = unit(frag)
        if not u: return None
        phones = u.get('telephone_numbers', [])
        return phones[0].replace(' ', '') if phones else None

    def test_northumbria_scbu_phone(self):
        self.assertEqual(self._phone("Northumbria Specialist"), '01916072017')

    def test_singleton_phone(self):
        self.assertEqual(self._phone("Singleton"), '01792285403')

    def test_ninewells_phone(self):
        self.assertEqual(self._phone("Ninewells"), '01382633840')

    def test_raigmore_phone(self):
        self.assertEqual(self._phone("Raigmore"), '01463704375')

    def test_princess_royal_maternity_phone(self):
        self.assertEqual(self._phone("Princess Royal Maternity"), '01414515221')

    def test_cumberland_infirmary_phone(self):
        self.assertEqual(self._phone("Cumberland Infirmary"), '01228814271')


class TestSearchIndexQuality(unittest.TestCase):
    """unit_name_full must correctly expand abbreviations for fuzzy search."""

    def test_q_dot_expands_to_queen(self):
        for u in DATA:
            if u['unit_name'].startswith('Q.'):
                with self.subTest(unit=u['unit_name']):
                    self.assertIn('Queen', u.get('unit_name_full', ''),
                        f"'Q.' not expanded in: {u['unit_name']}")

    def test_hosp_expands_to_hospital(self):
        for u in DATA:
            if ' Hosp' in u['unit_name'] and 'Hospital' not in u['unit_name']:
                with self.subTest(unit=u['unit_name']):
                    self.assertIn('Hospital', u.get('unit_name_full', ''),
                        f"'Hosp' not expanded in full name: {u['unit_name']}")

    def test_gen_expands_to_general(self):
        for u in DATA:
            if ' Gen ' in u['unit_name'] or u['unit_name'].endswith(' Gen'):
                with self.subTest(unit=u['unit_name']):
                    self.assertIn('General', u.get('unit_name_full', ''),
                        f"'Gen' not expanded in: {u['unit_name']}")

    def test_no_unit_name_full_is_empty(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                self.assertTrue(len(u.get('unit_name_full', '').strip()) > 0,
                    "unit_name_full is empty")

    def test_no_trust_full_is_empty(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                self.assertTrue(len(u.get('trust_full', '').strip()) > 0,
                    "trust_full is empty")

    def test_key_units_searchable_by_full_name(self):
        checks = [
            ("Queen Elizabeth",  lambda u: 'queen elizabeth' in u.get('unit_name_full','').lower()),
            ("Addenbrooke",      lambda u: 'addenbrooke' in (u.get('unit_name','') + u.get('unit_name_full','')).lower()),
            ("Norfolk",          lambda u: 'norfolk' in (u.get('unit_name','') + u.get('address','')).lower()),
        ]
        for term, fn in checks:
            with self.subTest(search_term=term):
                self.assertTrue(any(fn(u) for u in DATA),
                    f"'{term}' not findable in any unit")



class TestStrictODNEnumeration(unittest.TestCase):
    """Ensure network_odn only uses sanctioned region names."""

    VALID_ODNS = {
        'North West', 'South East', 'South West', 'Wales', 'Northern Ireland',
        'East Midlands', 'SSBC', 'London', 'Thames Valley & Wessex', 'Northern',
        'Scotland', 'East of England', 'Kent, Surrey & Sussex', 'Yorkshire & Humber',
        'West Midlands'
    }

    def test_odn_names_are_valid(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                self.assertIn(u.get('network_odn'), self.VALID_ODNS,
                    f"'{u['unit_name']}' has unrecognised ODN: {u.get('network_odn')}")


class TestContactNumberFormatting(unittest.TestCase):
    """Ensure telephone numbers arrays are well formed."""

    def test_telephone_numbers_is_array_of_strings(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                nums = u.get('telephone_numbers')
                self.assertIsInstance(nums, list, "telephone_numbers must be a list")
                for num in nums:
                    self.assertIsInstance(num, str, "Each telephone number must be a string")

    def test_no_identical_numbers_within_same_unit(self):
        for u in DATA:
            with self.subTest(unit=u['unit_name']):
                nums = u.get('telephone_numbers', [])
                stripped = [n.replace(' ','').replace('-','') for n in nums]
                self.assertEqual(len(stripped), len(set(stripped)),
                    f"'{u['unit_name']}' contains duplicate phone numbers within its array")


# ── Runner ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Original tests
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaCompleteness))
    suite.addTests(loader.loadTestsFromTestCase(TestNoDuplicates))
    suite.addTests(loader.loadTestsFromTestCase(TestGeocoding))
    suite.addTests(loader.loadTestsFromTestCase(TestClinicalPlausibility))
    suite.addTests(loader.loadTestsFromTestCase(TestNoPlaceholderStrings))
    suite.addTests(loader.loadTestsFromTestCase(TestPhoneNumberFormat))
    suite.addTests(loader.loadTestsFromTestCase(TestKnownUnits))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseCoverage))

    # Extended tests
    suite.addTests(loader.loadTestsFromTestCase(TestTransportConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestGeospatialClustering))
    suite.addTests(loader.loadTestsFromTestCase(TestCapabilityLogicConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestAddressQuality))
    suite.addTests(loader.loadTestsFromTestCase(TestPhoneUniqueness))
    suite.addTests(loader.loadTestsFromTestCase(TestRegionalCityPresence))
    suite.addTests(loader.loadTestsFromTestCase(TestSpotCheckPhoneNumbers))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchIndexQuality))
    suite.addTests(loader.loadTestsFromTestCase(TestStrictODNEnumeration))
    suite.addTests(loader.loadTestsFromTestCase(TestContactNumberFormatting))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
