import pytest
from tests import base
from girder.api.rest import RestException

'''Tests for the methods in dataone_register.py. Some of these tests use live requests, while others use
mocked JSON responses/data structures. '''


def setUpModule():

    base.enabledPlugins.append('wholetale')
    base.startServer()


def tearDownModule():

    base.stopServer()


class TestDataONERegister(base.TestCase):

    def test_find_initial_pid(self):
        from server.dataone_register import find_initial_pid

        # Test that the regex is working for search.dataone urls
        pid = 'https://search.dataone.org/#view/urn:uuid:7ec733c4-aa63-405a-a58d-1d773a9025a9'
        res = find_initial_pid(pid)
        assert res == 'urn:uuid:7ec733c4-aa63-405a-a58d-1d773a9025a9'

        # Test that the regex is working for paths coming from the coordinating node
        pid = 'https://cn.dataone.org/cn/v2/object/urn:uuid:6f5533ab-6508-4ac7-82a3-1df88ed4580e'
        res = find_initial_pid(pid)
        assert res == pid

        # Test that if nothing was found, None is returned
        bad_url = 'has2:"//badurl.bxwcom/a_bad_/url'
        res = find_initial_pid(bad_url)
        assert res == bad_url

    def test_find_resource_pid(self):
        from server.dataone_register import find_resource_pid

        # Test the case where no data object could be located
        with pytest.raises(RestException) as error:
            bad_url = 'https:"//badurl.com/a_bad_/url'
            find_resource_pid(bad_url)

    def test_get_package_files_metadata(self):
        ''' Test that the metadata in a package is getting added to the list of files'''
        from server.dataone_register import get_package_files

        full_meta_data = [{'identifier': 'urn:uuid:f438a8d5-7965-4ca2-aad6-88f694e5afe5', 'fileName': 'iso19139.xml',
        'formatId': 'http://www.isotc211.org/2005/gmd', 'formatType': 'METADATA', 'size': 14735,
        'title': 'Collaborative Research: A Synthesis of Existing and New Observations of Air-Snowpack Exchanges to'
                           ' Assess the Arctic',
        'documents': ['urn:uuid:f438a8d5-7965-4ca2-aad6-88f694e5afe5',
                   'resource_map_urn:uuid:23acf3bd-27c7-4736-a6ef-c141698d66b8',
                   'resource_map_urn:uuid:1570fb91-69e8-4c1d-9b9a-292edb5820af']}]

        data = []

        expected_result = {'iso19139.xml': {'size': 14735}}

        # In this case, the primary metadata object is the same as the metadata object
        fileList = get_package_files(data, full_meta_data, full_meta_data)
        assert fileList == expected_result


    def test_get_package_files(self):
        '''Test that the files in a package are getting correctly parsed. This is tested on
        https://search.dataone.org/#view/urn:uuid:15403304-6eb8-4ede-8a56-332a3e92bef8
        '''
        from server.dataone_register import get_package_files

        data = [{'identifier': 'urn:uuid:4eb73500-fa9b-46c2-a517-94c1a8b4afbb',
                            'fileName': 'HumanFootprint.ipynb', 'formatId': 'text/plain',
                            'formatType': 'DATA', 'size': 104524},
                           {'identifier': 'urn:uuid:06544a24-aae8-4b80-be4b-bb03711d9fd0',
                            'fileName': 'hfp_regions.csv', 'formatId': 'text/csv',
                            'formatType': 'DATA', 'size': 1757}]

        meta_data = [{'identifier': 'urn:uuid:15403304-6eb8-4ede-8a56-332a3e92bef8',
                                  'fileName': 'HumanFootprint_SASAP.xml',
                                  'formatId': 'eml://ecoinformatics.org/eml-2.1.1',
                                  'formatType': 'METADATA', 'size': 18648,
                                  'title': 'Global terrestrial Human Footprint maps for Alaska, 1993 and 2009,'
                                    'with SASAP regional subsetting',
                                  'documents': ['urn:uuid:15403304-6eb8-4ede-8a56-332a3e92bef8',
                                                'urn:uuid:4eb73500-fa9b-46c2-a517-94c1a8b4afbb',
                                                'urn:uuid:06544a24-aae8-4b80-be4b-bb03711d9fd0']}]

        expected_result = {'HumanFootprint.ipynb': {'size': 104524}, 'hfp_regions.csv': {'size': 1757},
                       'HumanFootprint_SASAP.xml': {'size': 18648}}

        fileList = get_package_files(data, meta_data, meta_data)

        assert fileList == expected_result


    def test_check_multiple_maps_empty(self):
        '''Test that we get an exception when no map was found.'''
        from server.dataone_register import check_multiple_maps

        with pytest.raises(RestException) as error:
            metadata =set()
            check_multiple_maps(metadata)

    def test_get_package_list_nested(self):
        # Test that we're getting all of the files in a nested package
        from server.dataone_register import get_package_list

        package = get_package_list("https://search.dataone.org/#view/urn:uuid:6f5533ab-6508-4ac7-82a3-1df88ed4580e")

        # Metadata that should be returned
        expected_result = {
            'Temperature and bio-geochemical data from Toolik Lake, Lake N2, Lake E1, Lake E5, and Lake E6,'
            ' North Slope, Alaska': {
                'fileList': [{'science_metadata.xml': {'size': 8940}}],
                'Carbon Dioxide and Methane profiles from Toolik Lake, Lake N2, Lake E1, Lake E5, and Lake E6,'
                ' North Slope, Alaska, 2012-2016': {
                    'fileList': [{'N2_lake_dissolved_gases_2012_2016.csv': {'size': 4141},
                                  'E6_lake_dissolved_gases_2012_2016.csv': {'size': 1769},
                                  'toolik_lake_dissolved_gases_2012_2016.csv': {'size': 9447},
                                  'E1_lake_dissolved_gases_2012_2016.csv': {'size': 4990},
                                  'E5_lake_dissolved_gases_2012_2016.csv': {'size': 4388},
                                  'science_metadata.xml': {'size': 26873}}]},
                'Time series of water temperature, specific conductance, and oxygen from Lake E5, North Slope,'
                ' Alaska': {
                    'fileList': [{'E5_metadata.xml': {'size': 8502}}],
                    'Time series of water temperature, specific conductance, and oxygen from Lake E5, North Slope,'
                    ' Alaska, 2012-2013': {
                        'fileList': [{'2013_summer_E5_temperature.csv': {'size': 3622122},
                                      '2012_2013_winter_E5_temperature.csv': {'size': 6959182},
                                      'E5_2013metadata.xml': {'size': 31522}}]},
                    'Time series of water temperature, specific conductance, and oxygen from Lake E5, North Slope,'
                    ' Alaska, 2014-2015': {
                        'fileList': [{'2015_summer_E5_temperature.csv': {'size': 3697500},
                                      '2014_2015_winter_E5_temperature.csv': {'size': 11630685},
                                      '2014_2015_winter_E5_dissoxy.csv': {'size': 1775633},
                                      '2014_2015_winter_E5_spconductance.csv': {'size': 483867},
                                      'E5_2015metadata.xml': {'size': 38791}}]},
                    'Time series of water temperature, specific conductance, and oxygen from Lake E5, North Slope,'
                    ' Alaska, 2013-2014': {
                        'fileList': [{'2013_2014_winter_E5_spconductance.csv': {'size': 467919},
                                      '2014_summer_E5_temperature.csv': {'size': 3239402},
                                      '2013_2014_winter_E5_dissoxy.csv': {'size': 1395110},
                                      '2013_2014_winter_E5_temperature.csv': {'size': 11365382},
                                      'E5_2014metadata.xml': {'size': 39491}}]},
                    'Time series of water temperature, specific conductance, and oxygen from Lake E5, North Slope,'
                    ' Alaska, 2015-2016': {
                        'fileList': [{'2015_2016_winter_E5_spconductance.csv': {'size': 522118},
                                      '2015_2016_winter_E5_dissoxy.csv': {'size': 1865414},
                                      '2016_summer_E5_temperature.csv': {'size': 2889371},
                                      '2015_2016_winter_E5_temperature.csv': {'size': 12259272},
                                      'E5_2016metadata.xml': {'size': 39461}}]}},
                'Time series of water temperature, specific conductance, and oxygen from Toolik Lake, North Slope,'
                ' Alaska': {
                    'fileList': [{'toolik_metadata.xml': {'size': 8506}}],
                    'Time series of water temperature, specific conductance, and oxygen from Toolik Lake, North Slope,'
                    ' Alaska, 2012-2013': {
                        'fileList': [{'2013_summer_toolik_temperature.csv': {'size': 6875617},
                                      '2012_2013_winter_toolik_temperature.csv': {'size': 19536076},
                                      '2012_2013_winter_toolik_spconductance.csv': {'size': 689738},
                                      'toolik_2013metadata.xml': {'size': 48909}}]},
                    'Time series of water temperature, specific conductance, and oxygen from Toolik Lake, North Slope,'
                    ' Alaska, 2013-2014': {
                        'fileList': [{'2013_2014_winter_toolik_temperature.csv': {'size': 16557796},
                                      '2013_2014_winter_toolik_dissoxy.csv': {'size': 3065075},
                                      '2014_summer_toolik_temperature.csv': {'size': 8152742},
                                      '2013_2014_winter_toolik_spconductance.csv': {'size': 1143165},
                                      'toolik_2014metadata.xml': {'size': 56269}}]},
                    'Time series of water temperature, specific conductance, and oxygen from Toolik Lake, North Slope,'
                    ' Alaska, 2014-2015': {
                        'fileList': [{'2014_2015_winter_toolik_dissoxy.csv': {'size': 2938042},
                                      '2015_summer_toolik_spconductance.csv': {'size': 326729},
                                      '2015_summer_toolik_dissoxy.csv': {'size': 422900},
                                      '2014_2015_winter_toolik_temperature.csv': {'size': 17568419},
                                      '2015_summer_toolik_temperature.csv': {'size': 7388577},
                                      '2014_2015_winter_toolik_spconductance.csv': {'size': 944978},
                                      'toolik_2015metadata.xml': {'size': 65009}}]},
                    'Time series of water temperature, specific conductance, and oxygen from Toolik Lake, North Slope,'
                    ' Alaska, 2015-2016': {
                        'fileList': [{'2015_2016_winter_toolik_spconductance.csv': {'size': 1508161},
                                      '2016_summer_toolik_temperature.csv': {'size': 6424024},
                                      '2015_2016_winter_toolik_dissoxy.csv': {'size': 3195361},
                                      '2016_summer_toolik_dissoxy.csv': {'size': 278700},
                                      '2015_2016_winter_toolik_temperature.csv': {'size': 20143003},
                                      'toolik_2016metadata.xml': {'size': 62748}}]}},
                'Temperature and bio-geochemical profiles from Toolik Lake, Lake N2, Lake E1, Lake E5, and Lake E6,'
                ' North Slope, Alaska, 2012-2016': {
                    'fileList': [{'E5_lake_physchem_2012_2016.csv': {'size': 14367},
                                  'N2_lake_physchem_2012_2016.csv': {'size': 9978},
                                  'toolik_lake_physchem_2012_2016.csv': {'size': 32570},
                                  'E1_lake_physchem_2012_2016.csv': {'size': 14970},
                                  'E6_lake_physchem_2012_2016.csv': {'size': 4422},
                                  'science_metadata.xml': {'size': 35150}}]},
                'Time series of water temperature, specific conductance, and oxygen from Lake N2, North Slope,'
                ' Alaska': {
                    'fileList': [{'N2_metadata.xml': {'size': 8502}}],
                    'Time series of water temperature, specific conductance, and oxygen from Lake N2, North Slope,' 
                    ' Alaska, 2015-2016': {
                        'fileList': [{'2015_2016_winter_N2_temperature.csv': {'size': 9175080},
                                      '2015_2016_winter_N2_spconductance.csv': {'size': 669063},
                                      '2015_2016_winter_N2_dissoxy.csv': {'size': 2274196},
                                      'N2_2016metadata.xml': {'size': 27618}}]},
                    'Time series of water temperature, specific conductance, and oxygen from Lake N2, North Slope,'
                    ' Alaska, 2012-2013': {
                        'fileList': [{'2013_summer_N2_temperature.csv': {'size': 3236585},
                                      '2013_summer_N2_spconductance.csv': {'size': 98037},
                                      '2012_2013_winter_N2_temperature.csv': {'size': 7884365},
                                      '2012_2013_winter_N2_spconductance.csv': {'size': 660777},
                                      '2012_2013_winter_N2_dissoxy.csv': {'size': 1342424},
                                      'N2_2013metadata.xml': {'size': 38906}}]},
                    'Time series of water temperature, specific conductance, and oxygen from Lake N2, North Slope,'
                    ' Alaska, 2014-2015': {
                        'fileList': [{'2014_2015_winter_N2_spconductance.csv': {'size': 764082},
                                      '2014_2015_winter_N2_temperature.csv': {'size': 8186731},
                                      '2014_2015_winter_N2_dissoxy.csv': {'size': 2041484},
                                      '2015_summer_N2_temperature.csv': {'size': 3959476},
                                      'N2_2015metadata.xml': {'size': 38880}}]},
                    'Time series of water temperature, specific conductance, and oxygen from Lake N2, North Slope,'
                    ' Alaska, 2013-2014': {
                        'fileList': [{'2013_2014_winter_N2_spconductance.csv': {'size': 805573},
                                      '2014_summer_N2_temperature.csv': {'size': 3985764},
                                      '2013_2014_winter_N2_temperature.csv': {'size': 8799847},
                                      '2013_2014_winter_N2_dissoxy.csv': {'size': 2199099},
                                      '2014_summer_N2_spconductance.csv': {'size': 109399},
                                      'N2_2014metadata.xml': {'size': 42453}}]}},
                'Time series of water temperature, specific conductance, and oxygen from Lake E6, North Slope,'
                ' Alaska': {
                    'fileList': [{'E6_metadata.xml': {'size': 8502}}],
                    'Time series of water temperature, specific conductance, and oxygen from Lake E6, North Slope,'
                    ' Alaska, 2012-2013': {
                        'fileList': [{'2013_summer_E6_temperature.csv': {'size': 1809400},
                                      '2012_2013_winter_E6_temperature.csv': {'size': 10530736},
                                      'E6_2013metadata.xml': {'size': 26487}}]},
                    'Time series of water temperature, specific conductance, and oxygen from Lake E6, North Slope,'
                    ' Alaska, 2013-2014': {
                        'fileList': [{'2013_2014_winter_E6_temperature.csv': {'size': 7576278},
                                      '2013_2014_winter_E6_spconductance.csv': {'size': 311796},
                                      '2014_summer_E6_temperature.csv': {'size': 2563014},
                                      '2013_2014_winter_E6_dissoxy.csv': {'size': 891254},
                                      'E6_2014metadata.xml': {'size': 33677}}]},
                    'Time series of water temperature, specific conductance, and oxygen from Lake E6, North Slope,'
                    ' Alaska, 2014-2015': {
                        'fileList': [{'2014_2015_winter_E6_dissoxy.csv': {'size': 798736},
                                      '2014_2015_winter_E6_temperature.csv': {'size': 7001630},
                                      '2015_summer_E6_temperature.csv': {'size': 2599637},
                                      '2014_2015_winter_E6_spconductance.csv': {'size': 294911},
                                      'E6_2015metadata.xml': {'size': 34381}}]},
                    'Time series of water temperature, specific conductance, and oxygen from Lake E6, North Slope,'
                    ' Alaska, 2015-2016': {
                        'fileList': [{'2016_summer_E6_temperature.csv': {'size': 1925158},
                                      '2015_2016_winter_E6_dissoxy.csv': {'size': 1197456},
                                      '2015_2016_winter_E6_temperature.csv': {'size': 6833526},
                                      '2015_2016_winter_E6_spconductance.csv': {'size': 503972},
                                      'E6_2016metadata.xml': {'size': 32344}}]}},
                'Time series of water temperature, specific conductance, and oxygen from Lake E1, North Slope,'
                ' Alaska': {
                    'fileList': [{'E1_metadata.xml': {'size': 8498}}],
                    'Time series of water temperature, specific conductance and oxygen from Lake E1, North Slope,'
                    ' Alaska, 2015-2016': {
                        'fileList': [{'2015_2016_winter_E1_spconductance.csv': {'size': 500013},
                                      '2015_2016_winter_E1_dissoxy.csv': {'size': 1396269},
                                      '2015_2016_winter_E1_temperature.csv': {'size': 11166136},
                                      'E1_2016metadata.xml': {'size': 26819}}]},
                    'Time series of water temperature, specific conductance and oxygen from Lake E1, North Slope,'
                    ' Alaska, 2013-2014': {
                        'fileList': [{'2013_2014_winter_E1_temperature.csv': {'size': 12183564},
                                      '2013_2014_winter_E1_spconductance.csv': {'size': 450249},
                                      '2014_summer_E1_temperature.csv': {'size': 4790928},
                                      '2014_summer_E1_spconductance.csv': {'size': 162291},
                                      '2013_2014_winter_E1_dissoxy.csv': {'size': 2131042},
                                      'E1_2014metadata.xml': {'size': 47376}}]},
                    'Time series of water temperature, specific conductance and oxygen from Lake E1, North Slope,'
                    ' Alaska, 2012-2013': {
                        'fileList': [{'2013_summer_E1_temperature.csv': {'size': 3782958},
                                      '2012_2013_winter_E1_temperature.csv': {'size': 11118770},
                                      'E1_2013metadata.xml': {'size': 32211}}]},
                    'Time series of water temperature, specific conductance and oxygen from Lake E1, North Slope,'
                    ' Alaska, 2014-2015': {
                        'fileList': [{'2014_2015_winter_E1_temperature.csv': {'size': 9679469},
                                      '2015_summer_E1_spconductance.csv': {'size': 183913},
                                      '2014_2015_winter_E1_dissoxy.csv': {'size': 1603002},
                                      '2014_2015_winter_E1_spconductance.csv': {'size': 586667},
                                      '2015_summer_E1_temperature.csv': {'size': 5687791},
                                      'E1_2015metadata.xml': {'size': 45972}}]}}}}



        assert package == expected_result

    def test_get_package_list_flat(self):
        # Test that we're getting all of the files in a non-nested package
        from server.dataone_register import get_package_list

        package = get_package_list('https://search.dataone.org/#view/urn:uuid:7ec733c4-aa63-405a-a58d-1d773a9025a9')

        assert package =={
            "Doctoral Dissertation Research: Mapping Community Exposure to Coastal Climate Hazards in the Arctic:"
             " A Case Study in Alaska's North Slope":
                 {'fileList':
                      [{'science_metadata.xml':
                            {'size': 8961}}],
                  'Arctic Slope Shoreline Change Risk Spatial Data Model, 2015-16':
                      {'fileList': [{'science_metadata.xml':
                                         {'size': 7577}}]},
                  'North Slope Borough shoreline change risk WebGIS usability workshop.':
                      {'fileList':
                           [{'science_metadata.xml':
                                 {'size': 7940}}]},
                  'Local community verification of shoreline change risks along the Alaskan Arctic Ocean coast'
                  ' (North Slope).':
                      {'fileList':
                           [{'science_metadata.xml':
                                 {'size': 14250}}]},
                  'Arctic Slope Shoreline Change Susceptibility Spatial Data Model, 2015-16':
                      {'fileList': [{'science_metadata.xml':
                                         {'size': 10491}}]}}}

