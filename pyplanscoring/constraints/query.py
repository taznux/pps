"""
Classes to implement Mayo DVH query format

based on:

https://rexcardan.github.io/ESAPIX/api/ESAPIX.Constraints.DVH.Query.html

"""
import re

from ..core.types import (DICOMType, DoseUnit, DoseValue,
                          DoseValuePresentation, QueryType, Units,
                          VolumePresentation)


class MayoRegex:
    UnitsDesired = r"\[(cc|%|(c?Gy)|)\]"
    QueryType = r"^(V|CV|DC|D|Mean|Max|Min|CI|HI|GI)"
    QueryValue = r"\d+(\.?)(\d+)?"
    QueryUnits = r"((cc)|%|(c?Gy))"
    Valid = r'(((V|CV|DC|D|CI|HI|GI)(\d+(\.?)(\d+)?((cc)|%|(c?Gy))))|(Mean|Max|Min))\[(cc|%|(c?Gy)|)\]'


class MayoQuery:
    def __init__(self):
        self._query_type = None
        self._query_units = None
        self._query_value = None
        self._units_desired = None
        self._query = None

    def read(self, query):
        mayo_query = MayoQueryReader().read(query)
        self.query_type = mayo_query.query_type
        self.query_units = mayo_query.query_units
        self.query_value = mayo_query.query_value
        self.units_desired = mayo_query.units_desired
        self.query = mayo_query
        return self

    @property
    def query(self):
        return self._query

    @query.setter
    def query(self, value):
        self._query = value

    @property
    def query_type(self):
        return self._query_type

    @query_type.setter
    def query_type(self, value):
        self._query_type = value

    @property
    def query_units(self):
        return self._query_units

    @query_units.setter
    def query_units(self, value):
        self._query_units = value

    @property
    def query_value(self):
        return self._query_value

    @query_value.setter
    def query_value(self, value):
        self._query_value = value

    @property
    def units_desired(self):
        return self._units_desired

    @units_desired.setter
    def units_desired(self, value):
        self._units_desired = value

    def to_string(self):
        return MayoQueryWriter().write(self)

    def __str__(self):
        return self.to_string()

    def __repr__(self):  # pragma: no cover
        return self.to_string()


class MayoQueryWriter:
    def write(self, mayo_query):
        """
             public static string Write(MayoQuery query)
                    {
                        var type = GetTypeString(query.query_type);
                        var qUnits = GetUnitString(query.query_units);
                        var qValue = query.query_value.to_string();
                        var dUnits = GetUnitString(query.units_desired);
                        return $"{type}{qValue}{qUnits}[{dUnits}]";
                    }
        """
        query_type = self.get_type_string(mayo_query.query_type)
        q_units = self.get_unit_string(mayo_query.query_units)
        q_value = self.get_value_string(mayo_query.query_value)
        d_units = self.get_unit_string(mayo_query.units_desired)

        return query_type + q_value + q_units + '[' + d_units + ']'

    @staticmethod
    def get_type_string(query_type):
        switch = {
            QueryType.COMPLIMENT_VOLUME: "CV",
            QueryType.DOSE_AT_VOLUME: "D",
            QueryType.DOSE_COMPLIMENT: "DC",
            QueryType.MAX_DOSE: "Max",
            QueryType.MEAN_DOSE: "Mean",
            QueryType.MIN_DOSE: "Min",
            QueryType.VOLUME_AT_DOSE: "V",
            QueryType.CI: "CI",
            QueryType.HI: "HI",
            QueryType.GI: "GI"
        }

        return switch.get(query_type)

    @staticmethod
    def get_value_string(query_value):
        if query_value:
            return ('%f' % query_value).rstrip('0').rstrip('.')
        else:
            return ''

    @staticmethod
    def get_unit_string(query_units):
        switch = {
            Units.CC: "cc",
            Units.CGY: "cGy",
            Units.GY: "Gy",
            Units.PERC: "%",
            Units.NA: '',
        }
        return switch.get(query_units)


class MayoQueryReader:
    """
     Class with methods to read a DVH query in "Mayo Format" (https://www.ncbi.nlm.nih.gov/pubmed/26825250)
    """

    def read(self, query):
        """
             Reads a full Mayo query string and converts it to a MayoQuery object
        :param query: string mayo query
        :return: Mayo Query object
        """
        if not self.is_valid(query):
            raise ValueError('Not a valid Mayo format')

        mq = MayoQuery()
        mq.query_type = self.read_query_type(query)
        mq.query_units = self.read_query_units(query)
        mq.units_desired = self.read_units_desired(query)
        mq.query_value = self.read_query_value(query)

        return mq

    @staticmethod
    def read_query_value(query):
        """
            Reads only the numerical value in the query (if one exists)
        :param query:
        :return:
        """
        match = re.search(MayoRegex.QueryValue, query)
        if not match:
            return None

        return float(match.group())

    @staticmethod
    def is_valid(query):
        # TODO debug it from Min, Max and Mean
        """
            Check if a query is valid
        :param query: Query string
        :return: boolean (True or False)
        """
        isMatch = re.search(MayoRegex.Valid, query, re.IGNORECASE)
        return bool(isMatch)

    @staticmethod
    def read_query_type(query):
        """
             read query type
        :param query: Query string
        :return: Query type
        """
        match = re.search(MayoRegex.QueryType, query)
        if not match:
            raise ValueError('Not a valid query type: %s' % query)

        switcher = {
            "DC": QueryType.DOSE_COMPLIMENT,
            "V": QueryType.VOLUME_AT_DOSE,
            "D": QueryType.DOSE_AT_VOLUME,
            "CV": QueryType.COMPLIMENT_VOLUME,
            "Min": QueryType.MIN_DOSE,
            "Max": QueryType.MAX_DOSE,
            "Mean": QueryType.MEAN_DOSE,
            "CI": QueryType.CI,
            "HI": QueryType.HI,
            "GI": QueryType.GI
        }

        return switcher.get(match.group(), QueryType.VOLUME_AT_DOSE)

    def read_query_units(self, query):
        """
            read Query units
        :param query: Query string
        :return: Unit
        """
        filtered = re.sub(MayoRegex.UnitsDesired, '', query)
        match = re.search(MayoRegex.QueryUnits, filtered, re.IGNORECASE)
        if not match:
            return self.convert_string_to_unit('NA')
        return self.convert_string_to_unit(match.group())

    def read_units_desired(self, query):
        match = re.search(MayoRegex.UnitsDesired, query, re.IGNORECASE)
        if not match:
            # dimensionless
            return self.convert_string_to_unit('NA')

        return self.convert_string_to_unit(match.group().replace('[',
                                                                 '').replace(
                                                                     ']', ''))

    @staticmethod
    def convert_string_to_unit(value):
        switcher = {
            "cc": Units.CC,
            "CC": Units.CC,
            "cGy": Units.CGY,
            "cGY": Units.CGY,
            "CGY": Units.CGY,
            "cgy": Units.CGY,
            "gy": Units.GY,
            "Gy": Units.GY,
            "GY": Units.GY,
            "%": Units.PERC,
            "NA": Units.NA,
            "": Units.NA
        }
        return switcher.get(value, Units.NA)


class QueryExtensions(MayoQuery):
    def __init__(self):
        super().__init__()

    def run_query(self, query, pi, ss):
        """
             This helps execute Mayo syntax queries against planning items
        :param query: MayoQuery string
        :param pi: PlanningItem
        :param ss: Structures dict
        :return: float value
        """

        d_pres = self.get_dose_presentation(query)
        v_pres = self.get_volume_presentation(query)
        dvh = pi.get_dvh_cumulative_data(ss, d_pres, v_pres)

        switch = {
            QueryType.DOSE_AT_VOLUME: self.query_dose,
            QueryType.DOSE_COMPLIMENT: self.query_dose_compliment,
            QueryType.VOLUME_AT_DOSE: self.query_volume,
            QueryType.COMPLIMENT_VOLUME: self.query_compliment_volume,
            QueryType.MAX_DOSE: self.query_max_dose,
            QueryType.MEAN_DOSE: self.query_mean_dose,
            QueryType.MIN_DOSE: self.query_min_dose,
            QueryType.CI: self.query_ci,
            QueryType.HI: self.query_hi,
            QueryType.GI: self.query_gi
        }

        metric_function = switch.get(query.query_type)

        # TODO add interface to target stats
        # If conformity index
        if query.query_type == QueryType.CI:
            return metric_function(pi, query, ss)

        # If gradient index
        if query.query_type == QueryType.GI:
            return metric_function(pi, query)

        return metric_function(dvh, query)

    @staticmethod
    def get_dose_presentation(query):
        """
            Returns the dose value presentation for this query, helps in acquiring the correct dvh
        :param query: MayoQuery
        :return: dose_value_presentation
        """
        # If volume query return query unit to dose unit
        switch = {
            Units.CGY: DoseValuePresentation.Absolute,
            Units.GY: DoseValuePresentation.Absolute,
            Units.PERC: DoseValuePresentation.Relative
        }

        query_types = [
            QueryType.COMPLIMENT_VOLUME, QueryType.VOLUME_AT_DOSE,
            QueryType.HI, QueryType.CI, QueryType.GI
        ]

        if query.query_type in query_types:
            return switch.get(query.query_units, DoseValuePresentation.Unknown)

        return switch.get(query.units_desired, DoseValuePresentation.Unknown)

    @staticmethod
    def get_dose_unit(query):
        """
             Returns the dose value presentation for this query, helps in acquiring the correct dvh
        :param query: MayoQuery
        :return: DoseValue.DoseUnit
        """
        switch = {
            Units.CGY: DoseUnit.cGy,
            Units.GY: DoseUnit.Gy,
            Units.PERC: DoseUnit.Percent
        }

        query_types = [
            QueryType.COMPLIMENT_VOLUME, QueryType.VOLUME_AT_DOSE,
            QueryType.HI, QueryType.CI, QueryType.GI
        ]
        # If volume query return query unit to dose unit
        if query.query_type in query_types:
            return switch.get(query.query_units, DoseUnit.Unknown)

        return switch.get(query.units_desired, DoseUnit.Unknown)

    @staticmethod
    def get_volume_presentation(query):
        """
            Returns the dose value presentation for this query, helps in acquiring the correct dvh
        :param query: MayoQuery
        :return: the volume presentation of the query
        """
        # If volume query return query unit to dose unit
        if query.query_type in [
                QueryType.COMPLIMENT_VOLUME, QueryType.VOLUME_AT_DOSE
        ]:
            switch = {
                Units.CC: VolumePresentation.absolute_cm3,
                Units.PERC: VolumePresentation.relative
            }

            return switch.get(query.units_desired, VolumePresentation.Unknown)

        switch = {
            Units.CC: VolumePresentation.absolute_cm3,
            Units.PERC: VolumePresentation.relative
        }

        return switch.get(query.query_units, VolumePresentation.Unknown)

    @staticmethod
    def query_dose(dvh, query):
        """
        :param dvh: DVHData object dvh
        :param query: MayoQuery
        :return: dose at volume
        """
        dose_unit = query.get_dose_unit(query)
        volume_presentation = query.get_volume_presentation(query)
        volume = query.query_value * volume_presentation
        dose = dvh.get_dose_at_volume(volume)
        return dose.get_dose(dose_unit)

    @staticmethod
    def query_dose_compliment(dvh, query):
        """

        :param dvh: DVHData object dvh
        :param query: MayoQuery
        :return: dose_compliment
        """
        dose_unit = query.get_dose_unit(query)
        volume_presentation = query.get_volume_presentation(query)
        volume = query.query_value * volume_presentation
        dose = dvh.get_dose_compliment(volume)
        return dose.get_dose(dose_unit)

    @staticmethod
    def query_max_dose(dvh, query):
        """
        :param dvh: DVHData object dvh
        :param query: MayoQuery
        :return: max dose at volume
        """
        max_dose = dvh.max_dose
        dose_unit = query.get_dose_unit(query)
        return max_dose.get_dose(dose_unit)

    @staticmethod
    def query_min_dose(dvh, query):
        """
        :param dvh: DVHData object dvh
        :param query: MayoQuery
        :return: min dose at volume
        """
        min_dose = dvh.min_dose
        dose_unit = query.get_dose_unit(query)
        return min_dose.get_dose(dose_unit)

    @staticmethod
    def query_mean_dose(dvh, query):
        """
        :param dvh: DVHData object dvh
        :param query: MayoQuery
        :return: mean dose at volume
        """
        mean_dose = dvh.mean_dose
        dose_unit = query.get_dose_unit(query)
        return mean_dose.get_dose(dose_unit)

    @staticmethod
    def query_volume(dvh, query):
        """

        :param dvh: DVHData object dvh
        :param query: MayoQuery
        :return: volume at dose
        """
        dose_unit = query.get_dose_unit(query)
        volume_presentation = query.get_volume_presentation(query)
        dose = DoseValue(query.query_value, dose_unit)
        volume = dvh.get_volume_at_dose(dose, volume_presentation)
        return volume

    @staticmethod
    def query_compliment_volume(dvh, query):
        """

        :param dvh: DVHData object dvh
        :param query: MayoQuery
        :return: compliment volume at dose
        """

        dose_unit = query.get_dose_unit(query)
        volume_presentation = query.get_volume_presentation(query)
        dose = DoseValue(query.query_value, dose_unit)
        volume = dvh.get_compliment_volume_at_dose(dose, volume_presentation)

        return volume

    @staticmethod
    def query_ci(pi, query, target_structure_name):
        """
            Calculates the Paddick conformity index (PMID 11143252) as Paddick CI = (TVPIV)2 / (TV x PIV).
            TVPIV = Target volume covered by Prescription Isodose volume
            TV = Target volume
        :param pi:
        :param query:
        :param target_structure_name:
        :return:
        """
        # TODO implement getting data only from structures
        external = None
        for k, v in pi.structures.items():
            if v['RTROIType'] == DICOMType.EXTERNAL:
                external = v
                break

        if external is None:  # pragma: no cover
            return None

        target_structure = pi.get_structure(target_structure_name)
        dose_unit = query.get_dose_unit(query)
        reference_dose = DoseValue(query.query_value, dose_unit)
        prescription_vol_isodose = pi.get_volume_at_dose(
            external['name'], reference_dose, VolumePresentation.absolute_cm3)

        target_vol_isodose = pi.get_volume_at_dose(
            target_structure_name, reference_dose,
            VolumePresentation.absolute_cm3)
        target_vol = target_structure[
            'volume'] * VolumePresentation.absolute_cm3

        ci = (target_vol_isodose * target_vol_isodose) / (
            target_vol * prescription_vol_isodose)
        return float(ci)

    @staticmethod
    def query_hi(dvh, query):
        dose_unit = query.get_dose_unit(query)
        reference_dose = DoseValue(query.query_value, dose_unit)
        volume99 = 99 * VolumePresentation.relative
        dose99 = dvh.get_dose_at_volume(volume99)
        volume1 = 1 * VolumePresentation.relative
        dose1 = dvh.get_dose_at_volume(volume1)

        h_i = (dose1 - dose99) / reference_dose

        return float(h_i)

    @staticmethod
    def query_gi(pi, query):
        """
            Calculates the Paddick gradient index (PMID 18503356) as Paddick GI = PIV_half/PIV

            PIV_half = Prescripition isodose volume at half by prescription isodose
            PIV = Prescripition isodose volume

        :param pi:
        :param query:
        :param target_structure_name:
        :return:
        """

        external = None
        for k, v in pi.structures.items():
            if v['RTROIType'] == DICOMType.EXTERNAL:
                external = v
                break

        if external is None:  # pragma: no cover
            return None

        dose_unit = query.get_dose_unit(query)
        reference_dose = DoseValue(query.query_value, dose_unit)
        vol_prescription_isodose = pi.get_volume_at_dose(
            external['name'], reference_dose, VolumePresentation.absolute_cm3)

        half_vol_prescription_isodose = pi.get_volume_at_dose(
            external['name'], reference_dose / 2.0,
            VolumePresentation.absolute_cm3)

        return float(
            half_vol_prescription_isodose /
            vol_prescription_isodose) if vol_prescription_isodose > 0 else None


class PyQueryExtensions(MayoQuery):
    def __init__(self):
        super().__init__()

    def run_query(self, query, pi, ss):
        """
             This helps execute Mayo syntax queries against planning items
        :param query: MayoQuery string
        :param pi: PlanningItem
        :param ss: Structures dict
        :return: float value
        """

        switch = {
            QueryType.DOSE_AT_VOLUME: self.query_dose,
            QueryType.DOSE_COMPLIMENT: self.query_dose_compliment,
            QueryType.VOLUME_AT_DOSE: self.query_volume,
            QueryType.COMPLIMENT_VOLUME: self.query_compliment_volume,
            QueryType.MAX_DOSE: self.query_max_dose,
            QueryType.MEAN_DOSE: self.query_mean_dose,
            QueryType.MIN_DOSE: self.query_min_dose,
            QueryType.CI: self.query_ci,
            QueryType.HI: self.query_hi,
            QueryType.GI: self.query_gi
        }

        metric_function = switch.get(query.query_type)

        return metric_function(query, pi, ss)

    def query_dose(self, query, pi, ss):
        """
            Gets dose at volume

        :param query: MayoQuery string
        :param pi: PlanningItem
        :param ss: Structures dict
        :return: float value
        """
        d_pres, dose_unit, v_pres = self.get_query_parameters(query)

        dvh = pi.get_dvh_cumulative_data(ss, d_pres, v_pres)
        volume = query.query_value * v_pres

        dose = dvh.get_dose_at_volume(volume)

        return dose.get_dose(dose_unit)

    def query_dose_compliment(self, query, pi, ss):
        """
            Gets dose compliment
        :param query: MayoQuery string
        :param pi: PlanningItem
        :param ss: Structures dict
        :return: float value
        """
        # units
        d_pres, dose_unit, v_pres = self.get_query_parameters(query)

        # dvh_data
        dvh = pi.get_dvh_cumulative_data(ss, d_pres, v_pres)
        volume = query.query_value * v_pres
        dose = dvh.get_dose_compliment(volume)

        return dose.get_dose(dose_unit)

    def query_max_dose(self, query, pi, ss):
        """
            Gets max dose at volume

        :param query: MayoQuery string
        :param pi: PlanningItem
        :param ss: Structures dict
        :return: float value
        """
        # units
        d_pres, dose_unit, v_pres = self.get_query_parameters(query)

        # dvh_data
        dvh = pi.get_dvh_cumulative_data(ss, d_pres, v_pres)
        max_dose = dvh.max_dose

        return max_dose.get_dose(dose_unit)

    def query_min_dose(self, query, pi, ss):
        """
            Gets min dose at volume

        :param query: MayoQuery string
        :param pi: PlanningItem
        :param ss: Structures dict
        :return: float value
        """
        # units
        d_pres, dose_unit, v_pres = self.get_query_parameters(query)

        # dvh_data
        dvh = pi.get_dvh_cumulative_data(ss, d_pres, v_pres)
        min_dose = dvh.min_dose

        return min_dose.get_dose(dose_unit)

    def query_mean_dose(self, query, pi, ss):
        """
            Gets mean dose at volume

        :param query: MayoQuery string
        :param pi: PlanningItem
        :param ss: Structures dict
        :return: float value
        """
        # units
        d_pres, dose_unit, v_pres = self.get_query_parameters(query)

        # dvh_data
        dvh = pi.get_dvh_cumulative_data(ss, d_pres, v_pres)
        mean_dose = dvh.mean_dose

        return mean_dose.get_dose(dose_unit)

    def query_volume(self, query, pi, ss):
        """
            Gets volume at dose

        :param query: MayoQuery string
        :param pi: PlanningItem
        :param ss: Structures dict
        :return: float value
        """
        d_pres, dose_unit, v_pres = self.get_query_parameters(query)

        # dvh_data
        dvh = pi.get_dvh_cumulative_data(ss, d_pres, v_pres)

        dose = DoseValue(query.query_value, dose_unit)
        volume = dvh.get_volume_at_dose(dose, v_pres)

        return volume

    def query_compliment_volume(self, query, pi, ss):
        """
            Gets compliment volume at dose

        :param query: MayoQuery string
        :param pi: PlanningItem
        :param ss: Structures dict
        :return: float value
        """

        d_pres, dose_unit, v_pres = self.get_query_parameters(query)

        # dvh_data
        dvh = pi.get_dvh_cumulative_data(ss, d_pres, v_pres)

        dose = DoseValue(query.query_value, dose_unit)
        volume = dvh.get_compliment_volume_at_dose(dose, v_pres)

        return volume

    def query_ci(self, query, pi, ss):
        """
            Calculates the Paddick conformity index (PMID 11143252) as Paddick CI = (TVPIV)2 / (TV x PIV).
            TVPIV = Target volume covered by Prescription Isodose volume
            TV = Target volume

        :param query: MayoQuery string
        :param pi: PlanningItem
        :param ss: Structures dict
        :return: float value
        """
        v_pres = VolumePresentation.absolute_cm3
        dose_unit = self.get_dose_unit(query)
        dv = DoseValue(query.query_value, dose_unit)
        ci = pi.get_ci(ss, dv, v_pres)

        return float(ci)

    def query_hi(self, query, pi, ss):
        """
            Gets homogeneity index.

        :param query: MayoQuery string
        :param pi: PlanningItem
        :param ss: Structures dict
        :return: float value
        """
        d_pres, dose_unit, v_pres = self.get_query_parameters(query)

        # dvh_data
        dvh = pi.get_dvh_cumulative_data(ss, d_pres, v_pres)

        reference_dose = DoseValue(query.query_value, dose_unit)
        volume99 = 99 * VolumePresentation.relative
        dose99 = dvh.get_dose_at_volume(volume99)
        volume1 = 1 * VolumePresentation.relative
        dose1 = dvh.get_dose_at_volume(volume1)

        h_i = (dose1 - dose99) / reference_dose

        return float(h_i)

    def query_gi(self, query, pi, ss=''):
        """
            Calculates the Paddick gradient index (PMID 18503356) as Paddick GI = PIV_half/PIV

            PIV_half = Prescripition isodose volume at half by prescription isodose
            PIV = Prescripition isodose volume

        :param query: MayoQuery string
        :param pi: PlanningItem
        :param ss: Structures dict
        :return: float value
        """

        v_pres = VolumePresentation.absolute_cm3
        dose_unit = self.get_dose_unit(query)
        dv = DoseValue(query.query_value, dose_unit)
        gi = pi.get_gi(ss, dv, v_pres)

        return gi

    @staticmethod
    def get_dose_presentation(query):
        """
            Returns the dose value presentation for this query, helps in acquiring the correct dvh
        :param query: MayoQuery
        :return: dose_value_presentation
        """
        # If volume query return query unit to dose unit
        switch = {
            Units.CGY: DoseValuePresentation.Absolute,
            Units.GY: DoseValuePresentation.Absolute,
            Units.PERC: DoseValuePresentation.Relative
        }

        query_types = [
            QueryType.COMPLIMENT_VOLUME, QueryType.VOLUME_AT_DOSE,
            QueryType.HI, QueryType.CI, QueryType.GI
        ]

        if query.query_type in query_types:
            return switch.get(query.query_units, DoseValuePresentation.Unknown)

        return switch.get(query.units_desired, DoseValuePresentation.Unknown)

    @staticmethod
    def get_dose_unit(query):
        """
             Returns the dose value presentation for this query, helps in acquiring the correct dvh
        :param query: MayoQuery
        :return: DoseValue.DoseUnit
        """
        switch = {
            Units.CGY: DoseUnit.cGy,
            Units.GY: DoseUnit.Gy,
            Units.PERC: DoseUnit.Percent
        }

        query_types = [
            QueryType.COMPLIMENT_VOLUME, QueryType.VOLUME_AT_DOSE,
            QueryType.HI, QueryType.CI, QueryType.GI
        ]
        # If volume query return query unit to dose unit
        if query.query_type in query_types:
            return switch.get(query.query_units, DoseUnit.Unknown)

        return switch.get(query.units_desired, DoseUnit.Unknown)

    @staticmethod
    def get_volume_presentation(query):
        """
            Returns the dose value presentation for this query, helps in acquiring the correct dvh
        :param query: MayoQuery
        :return: the volume presentation of the query
        """
        # If volume query return query unit to dose unit
        if query.query_type in [
                QueryType.COMPLIMENT_VOLUME, QueryType.VOLUME_AT_DOSE
        ]:
            switch = {
                Units.CC: VolumePresentation.absolute_cm3,
                Units.PERC: VolumePresentation.relative
            }

            return switch.get(query.units_desired, VolumePresentation.Unknown)

        switch = {
            Units.CC: VolumePresentation.absolute_cm3,
            Units.PERC: VolumePresentation.relative
        }

        return switch.get(query.query_units, VolumePresentation.Unknown)

    def get_query_parameters(self, query):
        """
            Get parameters from query
        :param query: mayo query
        :return: dose_presentation, dose_unit, volume presentation
        """
        d_pres = self.get_dose_presentation(query)
        v_pres = self.get_volume_presentation(query)
        dose_unit = self.get_dose_unit(query)
        return d_pres, dose_unit, v_pres
