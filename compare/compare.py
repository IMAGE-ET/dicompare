import iso8601
import datetime

class CompareError(RuntimeError):
    """Comparison error."""
    def __init__(self, msg, stack):
        """Constructor.

        Args:
        msg -- message, '@' character will be replaced by key stack
        stack -- list of keys to identify which element causes error
        """
        st = ""
        if len(stack) > 0:
            st = " at "+"".join(stack)
        msg = str.replace(msg,"@",st)
        super(RuntimeError,self).__init__(msg)
    pass

def compare(lhs, rhs, **kwargs):
    """Compares @lhs with @rhs.

    Keyword args:
    hooks -- instance or iterable of instances of hooks
    """

    if "hooks" not in kwargs:
        hooks = []
    elif not isinstance(kwargs["hooks"],list):
        hooks = [ kwargs["hooks"] ]

    if len(hooks) == 0 or not isinstance(hooks[-1],Default):
        hooks.append(Default())

    # calling internal recursive comparison function with empty key stack
    _internal_compare(lhs,rhs,[],hooks)

def _internal_compare(lhs, rhs, stack, hooks):
    """Compares @lhs with @rhs (recursive).

    Args:
    hooks -- instance or iterable of instances of hooks
    """
    for hook in hooks:
        if hook.condition(lhs, rhs):
            hook.compare(lhs, rhs, stack, hooks)
            break

class Hook:
    """Abstract class for hooks."""
    def condition(self, lhs, rhs, stack):
        """Determines whether hook should execute its comparison method."""
        raise NotImplementedError

    def compare(self, lhs, rhs, stack, hooks):
        """Executes comparison. This method should raise CompareError if
        two objects @lhs and @rhs are not considered equal."""
        raise NotImplementedError

class Default(Hook):
    """Default hook class. Handles dict, list and basic types (int,str,float)."""
    def __init__(self, **kwargs):
        """Constructor.

        Keyword args:
        match_order -- compare lists according to order of their elements
        match_type -- consider objects equal, only if they have same type
        """
        self.match_order = kwargs.get('match_order',True)
        self.match_type = kwargs.get('match_type',False)

    def condition(self, lhs, rhs):
        """Whether default hook should be run. It always returns True, so
        Default hook should be always the last of passed hooks."""
        return True

    def compare(self, lhs, rhs, stack, hooks):
        """Performs comparison."""
        triggered = False
        for (cond, comp) in Default._internal_hooks:
            if cond(self,lhs,rhs):
                triggered = True
                comp(self,lhs,rhs,stack,hooks)
                break

        if not triggered:
            raise CompareError("unknown data type comparison method@", stack)

    def _conddict(self, lhs, rhs):
        """Returns whether two objects are both dictionaries."""
        return type(lhs) == dict and type(rhs) == dict

    def _condlist(self, lhs, rhs):
        """Returns whether two objects are both lists."""
        return type(lhs) == list and type(rhs) == list

    def _condvalue(self, lhs, rhs):
        """Returns whether two objects are neither both dicts nor lists."""
        #TODO change this condition
        return True

    def _condnone(self, lhs, rhs):
        """Returns whether two objects are None."""
        return type(lhs) == type(None) and type(rhs) == type(None)

    def _compdict(self, lhs, rhs, stack, hooks):
        """Perform comparison of two dicts."""
        rhskeys = list(rhs.keys())
        for k in lhs.keys():
            stack.append(".{}".format(k))
            if k not in rhs:
                raise CompareError("value@ not found in rhs",stack)
            _internal_compare(lhs[k],rhs[k],stack,hooks)
            stack.pop()
            rhskeys.remove(k)

        if len(rhskeys) > 0:
            stack.append(rhskeys[0])
            raise CompareError("value@ not found in lhs",stack)

    def _complist(self, lhs, rhs, stack, hooks):
        """Perform comparison of two lists."""
        if len(lhs) != len(rhs):
            raise CompareError("lists@ have different lengths",stack)

        if self.match_order:
            for (i,v) in enumerate(lhs):
                stack.append("[{}]".format(i))
                _internal_compare(lhs[i],rhs[i],stack,hooks)
                stack.pop()
        else:
            rhskeys = list(range(len(rhs)))
            for (i,v) in enumerate(lhs):
                stack.append("[{}]".format(i))
                found = None
                for j in rhskeys:
                    try:
                        _internal_compare(lhs[i],rhs[j],stack,hooks)
                        found = j
                        break
                    except CompareError:
                        pass
                if (found != None):
                    rhskeys.remove(found)
                else:
                    raise CompareError("list element@ not found in rhs",stack)
                stack.pop()

    def _compvalue(self, lhs, rhs, stack, hooks):
        """Perform comparison of two objects which are neither both dicts nor lists."""
        if self.match_type and type(lhs) != type(rhs):
            raise CompareError("data types@ differs",stack)

        try:
            if type(rhs)(lhs) != rhs or lhs != type(lhs)(rhs):
                raise CompareError("values@ differs",stack)
        except (ValueError, TypeError):
            raise CompareError("values@ differs (not convertable)",stack)

    def _compnone(self, lhs, rhs, stack, hooks):
        """Perform comparison of two None. Easy stuff :)."""
        return True

    # internal hooks used in this hook. See compare() method.
    _internal_hooks = (
        (_conddict,  _compdict),
        (_condlist,  _complist),
        (_condnone,  _compnone),
        (_condvalue, _compvalue),
    )
