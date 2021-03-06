# Test methods with long descriptive names can omit docstrings
# pylint: disable=missing-docstring
import numpy as np
from scipy import sparse

from Orange.data import Table, Domain, ContinuousVariable, DiscreteVariable
from Orange.widgets.unsupervised.owmanifoldlearning import OWManifoldLearning
from Orange.widgets.tests.base import WidgetTest


class TestOWManifoldLearning(WidgetTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.iris = Table("iris")

    def setUp(self):
        self.widget = self.create_widget(
            OWManifoldLearning, stored_settings={"auto_apply": False})  # type: OWManifoldLearning

    def test_input_data(self):
        """Check widget's data"""
        self.assertEqual(self.widget.data, None)
        self.send_signal("Data", self.iris)
        self.assertEqual(self.widget.data, self.iris)
        self.send_signal("Data", None)
        self.assertEqual(self.widget.data, None)

    def test_output_data(self):
        """Check if data is on output after apply"""
        self.assertIsNone(self.get_output("Transformed data"))
        self.send_signal("Data", self.iris)
        self.widget.apply_button.button.click()
        self.assertIsInstance(self.get_output("Transformed data"), Table)
        self.send_signal("Data", None)
        self.widget.apply_button.button.click()
        self.assertIsNone(self.get_output("Transformed data"))

    def test_n_components(self):
        """Check the output for various numbers of components"""
        self.send_signal("Data", self.iris)
        for i in range(self.widget.n_components_spin.minimum(),
                       self.widget.n_components_spin.maximum()):
            self.assertEqual(self.widget.data, self.iris)
            self.widget.n_components_spin.setValue(i)
            self.widget.n_components_spin.onEnter()
            self.widget.apply_button.button.click()
            self._compare_tables(self.get_output("Transformed data"), i)

    def test_manifold_methods(self):
        """Check output for various manifold methods"""
        self.send_signal("Data", self.iris)
        n_comp = self.widget.n_components
        for i in range(len(self.widget.MANIFOLD_METHODS)):
            self.assertEqual(self.widget.data, self.iris)
            self.widget.manifold_methods_combo.activated.emit(i)
            self.widget.apply_button.button.click()
            self._compare_tables(self.get_output("Transformed data"), n_comp)

    def _compare_tables(self, _output, n_components):
        """Helper function for table comparison"""
        self.assertEqual((len(self.iris), n_components), _output.X.shape)
        np.testing.assert_array_equal(self.iris.Y, _output.Y)
        np.testing.assert_array_equal(self.iris.metas, _output.metas)

    def test_sparse_data(self):
        data = Table("iris")
        data.X = sparse.csr_matrix(data.X)
        self.assertTrue(sparse.issparse(data.X))
        self.widget.manifold_method_index = 2
        self.send_signal("Data", data)
        self.widget.apply_button.button.click()
        self.assertTrue(self.widget.Error.sparse_methods.is_shown())
        self.send_signal("Data", None)
        self.widget.apply_button.button.click()
        self.assertFalse(self.widget.Error.sparse_methods.is_shown())
        # GH 2158
        self.widget.manifold_method_index = 0
        self.assertEqual(
            'TSNE',
            self.widget.MANIFOLD_METHODS[self.widget.manifold_method_index].__name__)
        self.send_signal("Data", data)
        self.widget.apply_button.button.click()
        self.assertFalse(self.widget.Error.sparse_methods.is_shown())
        self.assertFalse(self.widget.Error.sparse_tsne_distance.is_shown())
        self.assertIsInstance(self.get_output('Transformed data'), Table)
        self.widget.params_widget.parameters['metric'] = 'chebyshev'
        self.widget.apply_button.button.click()
        self.assertTrue(self.widget.Error.sparse_tsne_distance.is_shown())

    def test_singular_matrices(self):
        """
        Handle singular matrices.
        GH-2228
        """
        table = Table(
            Domain(
                [ContinuousVariable("a"), ContinuousVariable("b")],
                class_vars=DiscreteVariable("c", values=["0", "1"])),
            list(zip(
                [1, 1, 1],
                [0, 1, 2],
                [0, 1, 1]))
        )
        self.send_signal("Data", table)
        self.widget.manifold_methods_combo.activated.emit(0)  # t-SNE
        self.widget.tsne_editor.metric_combo.activated.emit(4)  # Mahalanobis
        self.assertFalse(self.widget.Error.manifold_error.is_shown())
        self.widget.apply_button.button.click()
        self.assertTrue(self.widget.Error.manifold_error.is_shown())
