from cct import cct
import transforge as tf

def test(complex_string):
    return cct.parse(complex_string, *(tf.Source() for _ in range(10)))

expressions=[
    """
    1: R2(Obj, Count);
2: ObjectExtent; 
join_attr 2 1
    """
    ,
    """
     1: ObjectInfo(Count);        
        join_attr
            (get_attrL 1)
            (apply2 ratio (get_attrR 1)  (apply1
                (compose size deify)
                (get_attrL 1)
            ))
    """
    ,
    """
1: ObjectInfo(Ratio);
2: ObjectInfo(Nom);
arealinterpol
(getamounts 1)
(pi2 (get_attrL 2))
    """
    ,
    """
    set_union(
        3:ObjectInfo(Nom),
        set_union(
            1:ObjectInfo(Nom), 
            2:ObjectInfo(Nom)
            )
        )
    """
    ,
    """
    generateobjects (1: ObjectInfo(Nom))
    """
    ,
    """
    nbuild (1: ObjectInfo(Ratio))
    """
    ,
    """
1: Network(Ratio);
2: ObjectInfo(Nom);
3: ObjectInfo(Nom);        
           generateobjectsfromrel (nRoutes (get_attrL 2) (get_attrL 3) 1)
    """
,
"""
    subset (1: ObjectInfo(Nom)) (-: C(Nom))
"""
,
"""
        1: ObjectInfo(Ratio);     
            avg (getamounts 1)         
""",
"""
        1: ObjectInfo(Nom);
        2: ObjectInfo(Nom);
        subset
            1
            (pi1 (select
                eq
                (oTopo (get_attrL 1) (get_attrL 2))
                in
            ))
""",
"""
        1: Network(Ratio);
        2: ObjectInfo(Nom);
        3: ObjectInfo(Nom);
        join_attr
            (get_attrL 2)
            (groupbyL min (nDist (get_attrL 2) (get_attrL 3) 1))
"""
]

for e in expressions:
    print(test(e).tree())