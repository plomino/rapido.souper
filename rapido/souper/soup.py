from zope.interface import implements, alsoProvides
from zope.component import provideUtility, getMultiAdapter
from repoze.catalog.query import Eq
from souper.soup import get_soup, Record
try:
    from souper.plone.interfaces import ISoupRoot
    from souper.plone.locator import StorageLocator
except:
    from .interfaces import ISoupRoot
    from .locator import StorageLocator

from rapido.core.interfaces import IStorage, IRecordable, IDatabase

from .catalog import CatalogFactory

class SoupStorage(object):
    implements(IStorage)

    def __init__(self, context):
        self.context = context
        provideUtility(CatalogFactory(), name=self._get_id())

    def initialize(self):
        """ setup the storage
        """
        alsoProvides(self.context.root, ISoupRoot)
        locator = StorageLocator(self.context.root)
        locator.storage(self._get_id())
        self._soup = get_soup(self._get_id(), self.context.root)

    @property
    def soup(self):
        if not hasattr(self, '_soup'):
            self._soup = get_soup(self._get_id(), self.context.root)
        return self._soup

    def create(self):
        """ return a new document
        """
        record = Record()
        rid = self.soup.add(record)
        return getMultiAdapter(
            (self.soup.get(rid), IDatabase(self.context)),
            IRecordable)

    def get(self, uid=None):
        """ return an existing document
        """
        record = self.soup.get(uid)
        if not record:
            return None
        return getMultiAdapter(
            (record, IDatabase(self.context)),
            IRecordable)

    def save(self, doc):
        """ save a document
        """
        # the soup record stores item immediately
        pass

    def delete(self, doc):
        """ delete a document
        """
        del self.soup[doc.context]

    def search(self, query, sort_index=None, limit=None, sort_type=None,
            reverse=False, names=None, with_size=False):
        """ search for documents
        """
        records = self.soup.query(query, sort_index=sort_index, limit=limit,
            sort_type=sort_type, reverse=reverse, names=names,
            with_size=with_size)
        db = IDatabase(self.context)
        for record in records: 
            yield getMultiAdapter((record, db), IRecordable)

    def documents(self):
        for key in self.soup.data.keys():
            yield self.get(key)

    def reindex(self, doc):
        self.soup.reindex(records=[doc.context])

    def _get_id(self):
        return "rapido_%s" % (self.context.uid)