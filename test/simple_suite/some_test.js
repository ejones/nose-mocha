var assert = require('assert');

describe('Math', function() {
    it('should be consistent', function() {
        assert.equal(1, 1);
    });

    it('should be inconsistent', function() {
        assert.equal(1, 2);
    });
});

describe('Something', function() {
    it('should do stuff that breaks', function() {
        throw new Error;
    });
});
