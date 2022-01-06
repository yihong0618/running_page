from __future__ import division, absolute_import, print_function, unicode_literals
import functools

from stravalib import model
from stravalib.client import BatchedResultsIterator
from stravalib.tests.functional import FunctionalTestBase

class ResultIteratorTest(FunctionalTestBase):
        
    def setUp(self):
        super(ResultIteratorTest, self).setUp()
        self.protocol = self.client.protocol
        
    def test_limit_call(self):
        """ Test setting the limit in method call. """
        
        result_fetcher = functools.partial(self.protocol.get, '/athlete/activities')
        results = BatchedResultsIterator(entity=model.Activity, result_fetcher=result_fetcher, limit=10, per_page=2)
        results = list(results)
        self.assertEqual(10, len(results))
    
    def test_multiple_iterator_calls(self):
        """ Test multiple calls of the iterator. """
        
        result_fetcher = functools.partial(self.protocol.get, '/athlete/activities')
        results = BatchedResultsIterator(entity=model.Activity, result_fetcher=result_fetcher, limit=10, per_page=2)
        results.limit = 10
        results1 = list(results)
        results2 = list(results)
        
        self.assertEqual(10, len(results1))
        self.assertEqual(len(results1), len(results2))
    
    
    def test_limit_iterator(self):
        """ Test setting the limit on the iterator. """
        
        result_fetcher = functools.partial(self.protocol.get, '/athlete/activities')
        results = BatchedResultsIterator(entity=model.Activity, result_fetcher=result_fetcher, limit=10, per_page=2)
        results.limit = 10
        results = list(results)
        self.assertEqual(10, len(results))
            
        
        # TODO: use a mock here to figure out how many calls are happening under the hood.
                          
    def test_empty(self):
        """ Test iterating over empty results. """
        # Specify two thing that we happen to know will return 0 results
        def pretend_fetcher(page, per_page):
            return []
        
        ri = BatchedResultsIterator(entity=model.Shoe, result_fetcher=pretend_fetcher)
        results = list(ri)
        self.assertEqual(0, len(results))
    