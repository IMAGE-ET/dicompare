import iso8601
import datetime

class CompareError(RuntimeError):
    def __init__(self, msg, stack):
        st = ""
        if len(stack) > 0:
            st = " at "+"".join(stack)
        msg = str.replace(msg,"@",st)
        super(RuntimeError,self).__init__(msg)
    pass

def compare(lhs, rhs, **kwargs):
    if "hooks" not in kwargs:
        kwargs["hooks"] = [ Default() ]
    elif not isinstance(kwargs["hooks"],list):
        kwargs["hooks"] = [ kwargs["hooks"] ]

    _internal_compare(lhs,rhs,[],kwargs["hooks"])

def _internal_compare(lhs, rhs, stack, hooks):
    for hook in hooks:
        if hook.condition(lhs, rhs):
            hook.compare(lhs, rhs, stack, hooks)
            break

# abstract class for hooks
class Hook:
    # checks whether hook should be executed
    # if condiction is satisfied, execute() method will be called
    def condition(self, lhs, rhs, stack):
        raise NotImplementedError

    # performs comparation between values
    # this method should either accept values (consider them as equal)
    # or raise an CompareError
    def compare(self, lhs, rhs, stack, hooks):
        raise NotImplementedError

# default hook class which can also be subclassed
class Default(Hook):
    def __init__(self, **kwargs):
        self.match_order = kwargs.get('match_order',True)
        self.match_type = kwargs.get('match_type',False)

    def condition(self, lhs, rhs):
        return True

    def compare(self, lhs, rhs, stack, hooks):
        triggered = False
        for (cond, comp) in Default._internal_hooks:
            if cond(self,lhs,rhs):
                triggered = True
                comp(self,lhs,rhs,stack,hooks)
                break

        if not triggered:
            raise CompareError("unknown data type comprasion method@", stack)

    def _conddict(self, lhs, rhs):
        return type(lhs) == dict and type(rhs) == dict

    def _condlist(self, lhs, rhs):
        return type(lhs) == list and type(rhs) == list

    def _condvalue(self, lhs, rhs):
        #TODO change this condition
        return True

    def _condnone(self, lhs, rhs):
        return type(lhs) == type(None) and type(rhs) == type(None)

    def _compdict(self, lhs, rhs, stack, hooks):
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
        if self.match_type and type(lhs) != type(rhs):
            raise CompareError("data types@ differs",stack)

        try:
            if type(rhs)(lhs) != rhs or lhs != type(lhs)(rhs):
                raise CompareError("values@ differs",stack)
        except (ValueError, TypeError):
            raise CompareError("values@ differs (not convertable)",stack)

    def _compnone(self, lhs, rhs, stack, hooks):
        return True

    # static member
    _internal_hooks = (
        (_conddict,  _compdict),
        (_condlist,  _complist),
        (_condnone,  _compnone),
        (_condvalue, _compvalue),
    )

class ISO8601(Hook):
    def __init__(self, **kwargs):
        self.from_str = kwargs.get("from_str",True)
        self.tolerance = datetime.timedelta(seconds=kwargs.get("tolerance",0.01))

    def _getdatetime(self, o):
        if isinstance(o, datetime.datetime):
            return o
        elif isinstance(o,str) and self.from_str:
            try:
                return iso8601.parse_date(o)
            except iso8601.ParseError:
                return None
        return None

    def condition(self, lhs, rhs):
        #import pdb; pdb.set_trace()
        self.lhs_dt = self._getdatetime(lhs)
        self.rhs_dt = self._getdatetime(rhs)
        return self.lhs_dt and self.rhs_dt

    def compare(self, lhs, rhs, stack, hooks):
        if abs(self.lhs_dt - self.rhs_dt) > self.tolerance:
            raise CompareError("datetimes@ difference exceedes tolerance",stack)
