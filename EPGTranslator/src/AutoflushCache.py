# Implement a keyed-cache with elements that can be timed-out
# The time-out will be either the per-key or, if none given, a per-cache
# default relative value.
# Timeout flushes occur on add() or fetch() calls
#
import time

class AutoflushCache:
    def __init__(self, default_timeout, null_return=None):
        self.cache = {}         # key -> val pairs
        self.clear_time = []    # sorted (abs_timeout, key) tuples
        self.dflt_rel_timeout = abs(default_timeout)
        self.null_return = null_return

# Change the default timeout.
# Only affects newly added keys (since we don't store how values
# were originally set)
#
    def change_timeout(self, new_timeout):
        self.dflt_rel_timeout = abs(new_timeout)

# A routine to remove any out-of-date items.
# These can be found at the head of the clear_time array.
# This returns the current time (for internal-use convenience)!
#
    def flush(self):
        now = time.time()
        clear_to = str(int(now))
        ix = 0
        while ix < len(self.clear_time):
            nx = ix + 1
            if self.clear_time[ix][0] > clear_to: break
            ix = nx
        if ix > 0:  # Something to clear
            for kx in range(ix):    # Delete the key/vals
                del self.cache[self.clear_time[kx][1]]
# Then delete the clear times
            del self.clear_time[0:ix]
        return now

# Add a key/val pair with an optional key-specific absolute timeout.
# This calls flush, whence it gets the current time.
# Is allowed to ovrwrite an exisiting key.
#
    def add(self, key, val, abs_timeout=0):
        now = self.flush()
# Iff this key already exists we need to remove its related clear_time
# entry.
        if key in self.cache:
            self.clear_time.remove(key)
        self.cache[key] = val
        if abs_timeout > 0:
            until = str(int(abs_timeout))
        else:
            until = str(int(now + self.dflt_rel_timeout))
        ix = 0
        while ix < len(self.clear_time):
            nx = ix + 1
            if self.clear_time[ix][0] > until: break
            ix = nx
        self.clear_time.insert(ix, (until, key))

# Get the value for a key.
# Calls flush() before fetching.
# Returns the null_return if there is no such key.
#
    def fetch(self, key):
        self.flush()
        if key in self.cache:
            retval = self.cache[key]
        else:
            retval = self.null_return
        return retval

# Delete a key if present.
# Deleting a non-existent key is not an error
#
    def delete(self, key):
        if key in self.cache:
            del self.cache[key]
            self.clear_time.remove(key)

# Remove all keys
#
    def purge(self):
        self.cache = {}
        self.clear_time = []

# Destructor - probably what happens by default anyway...
#
    def __del__(self):
        self.purge()
