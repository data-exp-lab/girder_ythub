import ItemCollection from 'girder/collections/ItemCollection';

var RaftCollection = ItemCollection.extend({
    pageLimit: 20,
    altUrl: 'raft'
});

export default RaftCollection;
