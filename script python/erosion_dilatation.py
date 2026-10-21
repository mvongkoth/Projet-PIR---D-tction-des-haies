"""
Model exported as python.
Name : Modèle
Group : 
With QGIS : 34414
"""

from typing import Any, Optional

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingContext
from qgis.core import QgsProcessingFeedback, QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterFeatureSink
from qgis import processing


class Modle(QgsProcessingAlgorithm):

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.addParameter(QgsProcessingParameterVectorLayer('cosia_vecteur', 'CoSIA vecteur', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('distance_buffer_mettre_le_meme_que_le_buffer_negatif_mais_en_positif', 'Distance Buffer (mettre le meme que le buffer negatif mais en positif)', type=QgsProcessingParameterNumber.Double, defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('distance_buffer_negative', 'Distance Buffer Negative', type=QgsProcessingParameterNumber.Double, defaultValue=None))
        self.addParameter(QgsProcessingParameterString('labelcosia', 'label-cosia', multiLine=False, defaultValue='0'))
        self.addParameter(QgsProcessingParameterFeatureSink('BufferNegatif', 'buffer negatif', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('BufferPositif', 'buffer positif', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Haie', 'haie', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters: dict[str, Any], context: QgsProcessingContext, model_feedback: QgsProcessingFeedback) -> dict[str, Any]:
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        results = {}
        outputs = {}

        # Extraire par attribut
        alg_params = {
            'FIELD': 'label-cosia',
            'INPUT': parameters['cosia_vecteur'],
            'OPERATOR': 0,  # =
            'VALUE': parameters['labelcosia'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtraireParAttribut'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Tampon negatif
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': parameters['distance_buffer_negative'],
            'END_CAP_STYLE': 0,  # Rond
            'INPUT': outputs['ExtraireParAttribut']['OUTPUT'],
            'JOIN_STYLE': 0,  # Rond
            'MITER_LIMIT': 2,
            'SEGMENTS': 10,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': parameters['BufferNegatif']
        }
        outputs['TamponNegatif'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['BufferNegatif'] = outputs['TamponNegatif']['OUTPUT']

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Tampon positif
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': parameters['distance_buffer_mettre_le_meme_que_le_buffer_negatif_mais_en_positif'],
            'END_CAP_STYLE': 0,  # Rond
            'INPUT': outputs['TamponNegatif']['OUTPUT'],
            'JOIN_STYLE': 0,  # Rond
            'MITER_LIMIT': 2,
            'SEGMENTS': 10,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': parameters['BufferPositif']
        }
        outputs['TamponPositif'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['BufferPositif'] = outputs['TamponPositif']['OUTPUT']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Différence symétrique
        alg_params = {
            'GRID_SIZE': None,
            'INPUT': outputs['ExtraireParAttribut']['OUTPUT'],
            'OVERLAY': outputs['TamponPositif']['OUTPUT'],
            'OVERLAY_FIELDS_PREFIX': None,
            'OUTPUT': parameters['Haie']
        }
        outputs['DiffrenceSymtrique'] = processing.run('native:symmetricaldifference', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Haie'] = outputs['DiffrenceSymtrique']['OUTPUT']
        return results

    def name(self) -> str:
        return 'Modèle'

    def displayName(self) -> str:
        return 'Modèle'

    def group(self) -> str:
        return ''

    def groupId(self) -> str:
        return ''

    def createInstance(self):
        return self.__class__()
