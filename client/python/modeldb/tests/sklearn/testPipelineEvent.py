import unittest
import sys
from ModelDbSyncerTest import SyncerTest

import modeldb.tests.utils as utils
from modeldb.thrift.modeldb import ttypes as modeldb_types
from modeldb.sklearn_native.ModelDbSyncer import *

from sklearn import linear_model
from sklearn.pipeline import Pipeline
from sklearn import decomposition

import pandas as pd

FMIN = sys.float_info.min
FMAX = sys.float_info.max

class TestPipelineEvent(unittest.TestCase):
    @classmethod
    def setUp(self):
        name = "logistic-test"
        author = "srinidhi"
        description = "income-level logistic regression"
        SyncerObj = SyncerTest(
            NewOrExistingProject(name, author, description),
            DefaultExperiment(),
            NewExperimentRun("Abc"))

        #Creating the pipeline
        pca = decomposition.PCA()
        lr = linear_model.LinearRegression()
        pipe = Pipeline(steps=[('pca', pca), ('logistic', lr)])
        model = linear_model.LinearRegression()
        np.random.seed(0)
        X = pd.DataFrame(np.random.randint(0,100,size=(100, 2)), columns=list('AB'))
        y = pd.DataFrame(np.random.randint(0,100,size=(100, 1)), columns=['output'])
        X.tag("digits-dataset")
        pipe.tag("pipeline with pca + logistic")
        pca.tag("decomposition PCA")
        lr.tag("basic linear reg")
        SyncerTest.instance.clearBuffer()
        pipe.fitSync(X,y)
        events = SyncerTest.instance.sync()
        self.pipelineEvent = events[0]
        
    def test_pipeline_construction(self):
        utils.validate_pipeline_event_struct(self.pipelineEvent, self)

    def test_overall_pipeline_fit_event(self):
        fitEvent = self.pipelineEvent.pipelineFit
        utils.validate_fit_event_struct(fitEvent, self)
        transformer = fitEvent.model
        expected_transformer = modeldb_types.Transformer(
            -1,
            [0.0],
            'Pipeline',
            'pipeline with pca + logistic')
        utils.is_equal_transformer(transformer, expected_transformer, self)

        df = fitEvent.df
        expected_df = modeldb_types.DataFrame(
            -1, 
            [
                modeldb_types.DataFrameColumn('A', 'int64'), 
                modeldb_types.DataFrameColumn('B', 'int64'), 
            ],
            100,
            'digits-dataset')
        utils.is_equal_dataframe(df, expected_df, self)

        spec = fitEvent.spec
        expected_spec = modeldb_types.TransformerSpec(
            -1, 
            'Pipeline',
            ['A', 'B'],
            [
                modeldb_types.HyperParameter('logistic__n_jobs', '1', 'int', FMIN, FMAX), 
                modeldb_types.HyperParameter('pca__copy', 'True', 'bool', FMIN, FMAX), 
                modeldb_types.HyperParameter('pca__n_components', 'None', 'NoneType', FMIN, FMAX), 
                modeldb_types.HyperParameter('logistic__fit_intercept', 'True', 'bool', FMIN, FMAX), 
                modeldb_types.HyperParameter('pca__whiten', 'False', 'bool', FMIN, FMAX), 
                modeldb_types.HyperParameter('steps', "[('pca', PCA(copy=True, n_components=None, whiten=False)), ('logistic', LinearRegression(copy_X=True, fit_intercept=True, n_jobs=1, normalize=False))]", 'list', FMIN, FMAX),
                modeldb_types.HyperParameter('logistic', 'LinearRegression(copy_X=True, fit_intercept=True, n_jobs=1, normalize=False)', 'LinearRegression', FMIN, FMAX), 
                modeldb_types.HyperParameter('pca', 'PCA(copy=True, n_components=None, whiten=False)', 'PCA', FMIN, FMAX),
                modeldb_types.HyperParameter('logistic__normalize', 'False', 'bool', FMIN, FMAX),
                modeldb_types.HyperParameter('logistic__copy_X', 'True', 'bool', FMIN, FMAX)
            ],
            'pipeline with pca + logistic')
        utils.is_equal_transformer_spec(spec, expected_spec, self)

        self.assertItemsEqual(fitEvent.featureColumns, ['A', 'B'])

    def test_pipeline_fit_stages(self):
        fitStages = self.pipelineEvent.fitStages
        utils.validate_pipeline_fit_stages(fitStages, self)
        self.assertEqual(len(fitStages), 2)

    def test_pipeline_first_fit_stage(self):
        fitStages = self.pipelineEvent.fitStages
        fitEvent1 = fitStages[0].fe
        # First Stage
        transformer = fitEvent1.model
        expected_transformer = modeldb_types.Transformer(
            -1,
            [0.0],
            'PCA',
            'decomposition PCA')
        utils.is_equal_transformer(transformer, expected_transformer, self)

        df = fitEvent1.df
        expected_df = modeldb_types.DataFrame(
            -1, 
            [
                modeldb_types.DataFrameColumn('A', 'int64'), 
                modeldb_types.DataFrameColumn('B', 'int64'), 
            ],
            100,
            'digits-dataset')
        utils.is_equal_dataframe(df, expected_df, self)

        spec = fitEvent1.spec
        expected_spec = modeldb_types.TransformerSpec(
            -1, 
            'PCA',
            ['A', 'B'],
            [
                modeldb_types.HyperParameter('copy', 'True', 'bool', FMIN, FMAX), 
                modeldb_types.HyperParameter('n_components', 'None', 'NoneType', FMIN, FMAX), 
                modeldb_types.HyperParameter('whiten', 'False', 'bool', FMIN, FMAX), 
            ],
            'decomposition PCA')
        utils.is_equal_transformer_spec(spec, expected_spec, self)

        self.assertItemsEqual(fitEvent1.featureColumns, ['A', 'B'])

    def test_pipeline_second_fit_stage(self):
        fitStages = self.pipelineEvent.fitStages
        fitEvent2 = fitStages[1].fe
        # Second Stage
        transformer = fitEvent2.model
        expected_transformer = modeldb_types.Transformer(
            -1,
            [0.08764694, 0.04159237],
            'LinearRegression',
            'basic linear reg')
        utils.is_equal_transformer(transformer, expected_transformer, self)

        df = fitEvent2.df
        expected_df = modeldb_types.DataFrame(
            -1, 
            [],
            100,
            '')
        utils.is_equal_dataframe(df, expected_df, self)

        spec = fitEvent2.spec
        expected_spec = modeldb_types.TransformerSpec(
            -1, 
            'LinearRegression',
            [],
            [
                modeldb_types.HyperParameter('copy_X', 'True', 'bool', FMIN, FMAX), 
                modeldb_types.HyperParameter('normalize', 'False', 'bool', FMIN, FMAX), 
                modeldb_types.HyperParameter('n_jobs', '1', 'int', FMIN, FMAX), 
                modeldb_types.HyperParameter('fit_intercept', 'True', 'bool', FMIN, FMAX)
            ],
            'basic linear reg')
        utils.is_equal_transformer_spec(spec, expected_spec, self)

    def test_pipeline_transform_stages(self):
        transformStages = self.pipelineEvent.transformStages
        utils.validate_pipeline_transform_stages(transformStages, self)
        self.assertEqual(len(transformStages), 1)

    def test_pipeline_first_transform_stage(self):
        transformStages = self.pipelineEvent.transformStages
        transformEvent1 = transformStages[0].te

        transformer = transformEvent1.transformer
        expected_transformer = modeldb_types.Transformer(
            -1,
            [0.0],
            'PCA',
            'decomposition PCA')
        utils.is_equal_transformer(transformer, expected_transformer, self)

        old_df = transformEvent1.oldDataFrame
        expected_old_df = modeldb_types.DataFrame(
            -1,
            [
                modeldb_types.DataFrameColumn('A', 'int64'), 
                modeldb_types.DataFrameColumn('B', 'int64'), 
            ],
            100,
            'digits-dataset')
        utils.is_equal_dataframe(expected_old_df, old_df, self)

        new_df = transformEvent1.newDataFrame
        expected_new_df = modeldb_types.DataFrame(
            -1,
            [
                modeldb_types.DataFrameColumn('0', 'float64'),
                modeldb_types.DataFrameColumn('1', 'float64'),
            ],
            100,
            '')
        utils.is_equal_dataframe(expected_new_df, new_df, self)

if __name__ == '__main__':
    unittest.main()