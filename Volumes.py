"""
Model exported as python.
Name : Volumenes
Group : Cálculos
With QGIS : 32201
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterDefinition
from qgis.core import QgsExpression
import processing


class Volumenes(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('Area', 'Area', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('PRE', 'PRE', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('POST', 'POST', defaultValue=None))
        param = QgsProcessingParameterString('CampodeNombres', 'Campo de Nombres', optional=True, multiLine=False, defaultValue='LABEL')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber('Densidad', 'Densidad', optional=True, type=QgsProcessingParameterNumber.Double, minValue=0, defaultValue=2.1)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterFile('EstiloRaster', 'Estilo Raster', optional=True, behavior=QgsProcessingParameterFile.File, fileFilter='Estilos (*.qml)', defaultValue='D:\\QGIS Datos\\Volumen_diferencias.qml')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterFile('EstiloVector', 'Estilo Vector', behavior=QgsProcessingParameterFile.File, fileFilter='Todos los archivos (*.qml)', defaultValue='D:\\QGIS Datos\\Acopios.qml')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        self.addParameter(QgsProcessingParameterNumber('Resolucion', 'Resolucion', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1.79769e+308, defaultValue=0.05))
        self.addParameter(QgsProcessingParameterRasterDestination('Diferencia', 'Diferencia', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Volumenes', 'Volumenes', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(18, model_feedback)
        results = {}
        outputs = {}

        # Cortar_POST
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Usar el tipo de datos de la capa de entrada
            'EXTRA': '',
            'INPUT': parameters['POST'],
            'KEEP_RESOLUTION': False,
            'MASK': parameters['Area'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'SET_RESOLUTION': True,
            'SOURCE_CRS': 'ProjectCrs',
            'TARGET_CRS': 'ProjectCrs',
            'X_RESOLUTION': parameters['Resolucion'],
            'Y_RESOLUTION': parameters['Resolucion'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Cortar_post'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Cortar_PRE
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Usar el tipo de datos de la capa de entrada
            'EXTRA': '',
            'INPUT': parameters['PRE'],
            'KEEP_RESOLUTION': False,
            'MASK': parameters['Area'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'SET_RESOLUTION': True,
            'SOURCE_CRS': 'ProjectCrs',
            'TARGET_CRS': 'ProjectCrs',
            'X_RESOLUTION': parameters['Resolucion'],
            'Y_RESOLUTION': parameters['Resolucion'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Cortar_pre'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # DIF
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': None,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': QgsExpression("'(A > 0)*(B > 0)*(A - B)'").evaluate(),
            'INPUT_A': outputs['Cortar_post']['OUTPUT'],
            'INPUT_B': outputs['Cortar_pre']['OUTPUT'],
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,  # Float32
            'OUTPUT': parameters['Diferencia']
        }
        outputs['Dif'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Diferencia'] = outputs['Dif']['OUTPUT']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Establecer estilo para capa ráster
        alg_params = {
            'INPUT': outputs['Dif']['OUTPUT'],
            'STYLE': parameters['EstiloRaster']
        }
        outputs['EstablecerEstiloParaCapaRster'] = processing.run('qgis:setstyleforrasterlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # CAMPO_TOTAL
        alg_params = {
            'COLUMN_PREFIX': 'TOTAL_',
            'INPUT': parameters['Area'],
            'INPUT_RASTER': outputs['Dif']['OUTPUT'],
            'RASTER_BAND': 1,
            'STATISTICS': [1],  # Suma
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Campo_total'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # TERRA
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': None,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': QgsExpression("'(A - B)*((A - B)>0)'").evaluate(),
            'INPUT_A': outputs['Cortar_post']['OUTPUT'],
            'INPUT_B': outputs['Cortar_pre']['OUTPUT'],
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,  # Float32
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Terra'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # CAMPO_TERRA
        alg_params = {
            'COLUMN_PREFIX': 'TERRA_',
            'INPUT_RASTER': outputs['Terra']['OUTPUT'],
            'INPUT_VECTOR': outputs['Campo_total']['OUTPUT'],
            'RASTER_BAND': 1,
            'STATISTICS': [1],  # Suma
        }
        outputs['Campo_terra'] = processing.run('native:zonalstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # DESMO
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': None,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': QgsExpression("'(A - B)*((A - B)<0)'").evaluate(),
            'INPUT_A': outputs['Cortar_post']['OUTPUT'],
            'INPUT_B': outputs['Cortar_pre']['OUTPUT'],
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,  # Float32
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Desmo'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # CAMPO_DESMO
        alg_params = {
            'COLUMN_PREFIX': 'DESMO_',
            'INPUT_RASTER': outputs['Desmo']['OUTPUT'],
            'INPUT_VECTOR': outputs['Campo_terra']['INPUT_VECTOR'],
            'RASTER_BAND': 1,
            'STATISTICS': [1],  # Suma
        }
        outputs['Campo_desmo'] = processing.run('native:zonalstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Rehacer campos1
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"TOTAL_sum"* @Resolucion ^2','length': 0,'name': 'TOTAL','precision': 3,'type': 6},{'expression': '"DESMO_sum"* @Resolucion ^2','length': 0,'name': 'DESMO','precision': 3,'type': 6},{'expression': '"TERRA_sum"* @Resolucion ^2','length': 0,'name': 'TERRA','precision': 3,'type': 6}],
            'INPUT': outputs['Campo_desmo']['INPUT_VECTOR'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RehacerCampos1'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Conditional branch
        alg_params = {
        }
        outputs['ConditionalBranch'] = processing.run('native:condition', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Rehacer campos DENS LABEL
        alg_params = {
            'FIELDS_MAPPING': [{'expression': 'attribute( @CampodeNombres )','length': 0,'name': 'LABEL','precision': 0,'type': 10},{'expression': '"TOTAL_sum"* @Resolucion ^2','length': 0,'name': 'TOTAL','precision': 3,'type': 6},{'expression': '"DESMO_sum"* @Resolucion ^2','length': 0,'name': 'DESMO','precision': 3,'type': 6},{'expression': '"TERRA_sum"* @Resolucion ^2','length': 0,'name': 'TERRA','precision': 3,'type': 6},{'expression': '("TOTAL_sum"* @Resolucion ^2)* @Densidad ','length': 0,'name': 'TONS','precision': 3,'type': 6}],
            'INPUT': outputs['Campo_desmo']['INPUT_VECTOR'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RehacerCamposDensLabel'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Rehacer campos DENS
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"TOTAL_sum"* @Resolucion ^2','length': 0,'name': 'TOTAL','precision': 3,'type': 6},{'expression': '"DESMO_sum"* @Resolucion ^2','length': 0,'name': 'DESMO','precision': 3,'type': 6},{'expression': '"TERRA_sum"* @Resolucion ^2','length': 0,'name': 'TERRA','precision': 3,'type': 6},{'expression': ' @Densidad * "TOTAL_sum"* @Resolucion ^2','length': 0,'name': 'TONS','precision': 3,'type': 6}],
            'INPUT': outputs['Campo_desmo']['INPUT_VECTOR'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RehacerCamposDens'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Rehacer campos2
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"TOTAL"','length': 0,'name': 'TOTAL','precision': 3,'type': 6},{'expression': '"DESMO"','length': 0,'name': 'DESMO','precision': 3,'type': 6},{'expression': '"TERRA"','length': 0,'name': 'TERRA','precision': 3,'type': 6}],
            'INPUT': outputs['RehacerCampos1']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RehacerCampos2'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Combinar capas vectoriales
        alg_params = {
            'CRS': 'ProjectCrs',
            'LAYERS': QgsExpression(' if(   @Densidad >0 AND length( @CampodeNombres )=0, @Rehacer_campos_DENS_OUTPUT  ,if( @Densidad =0 AND length( @CampodeNombres )>0,  @Rehacer_campos_LABEL_OUTPUT , if( @Densidad >0 AND length( @CampodeNombres )>0, @Rehacer_campos_DENS_LABEL_OUTPUT , @Rehacer_campos1_OUTPUT ) ))').evaluate(),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CombinarCapasVectoriales'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Rehacer campos LABEL
        alg_params = {
            'FIELDS_MAPPING': [{'expression': 'attribute( @CampodeNombres )','length': 0,'name': 'LABEL','precision': 0,'type': 10},{'expression': '"TOTAL_sum"* @Resolucion ^2','length': 0,'name': 'TOTAL','precision': 3,'type': 6},{'expression': '"DESMO_sum"* @Resolucion ^2','length': 0,'name': 'DESMO','precision': 3,'type': 6},{'expression': '"TERRA_sum"* @Resolucion ^2','length': 0,'name': 'TERRA','precision': 3,'type': 6}],
            'INPUT': outputs['Campo_desmo']['INPUT_VECTOR'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RehacerCamposLabel'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Quitar campo(s)
        alg_params = {
            'COLUMN': QgsExpression("'layer;path'").evaluate(),
            'INPUT': outputs['CombinarCapasVectoriales']['OUTPUT'],
            'OUTPUT': parameters['Volumenes']
        }
        outputs['QuitarCampos'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Volumenes'] = outputs['QuitarCampos']['OUTPUT']

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Establecer estilo para capa vectorial
        alg_params = {
            'INPUT': outputs['QuitarCampos']['OUTPUT'],
            'STYLE': parameters['EstiloVector']
        }
        outputs['EstablecerEstiloParaCapaVectorial'] = processing.run('qgis:setstyleforvectorlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'Volumenes'

    def displayName(self):
        return 'Volumenes'

    def group(self):
        return 'Cálculos'

    def groupId(self):
        return 'Cálculos'

    def createInstance(self):
        return Volumenes()
