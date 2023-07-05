from cct import cct
import transforge as tf

def test(complex_string):
    return cct.parse(complex_string, *(tf.Source() for _ in range(10)))

expressions=[
"""    1: ObjectInfo(Ratio);     
    join_attr      
    (nest2 (objectfromobjects (pi1 1))  (merge (pi1 (getamounts 1))))
    (nest2 (objectfromobjects (pi1 1)) (avg (getamounts 1))) 
    """
    ,
    """
        1: R2(Obj, Count);
        2: ObjectInfo(_);
        join_attr (get_attrL 2) 1
    """,
    """
        1: Field(Nom);
    2: ObjectInfo(Nom);
    join_attr
            (get_attrL 2)
            (apply1 
                (compose size pi1) 
                (apply1 
                    (compose (subset (1)) deify) 
                    (get_attrL 2)
                )
            )
    """
    ,
    """
    1: Network(Ratio);
2: ObjectInfo(Nom);
3: ObjectInfo(Nom);        
           nRoutes (get_attrL 2) (get_attrL 3) 1
    """,
    """
            1: ObjectInfo(Nom);
        2: ObjectInfo(Nom);
        subset
            1
            (pi1 (select
                leq
                (oDist (get_attrL 1) (get_attrL 2))
                (-:Ratio)
            ))
    """,
    """
    1:Ratio;
    2:R2(Obj, Reg);
    3:Reg;
     apply1(
        leq(1),
        groupbyL(min, loDist(deify(3), 2)))
    """
    ,
    """
    apply2 ratio (1: Amounts(Ratio)) (2: Amounts(Ratio))
    """
    ,
    """
    1: ObjectInfo(Ratio);
    2: ObjectInfo(Nom);
    join_attr
    (get_attrL 2)
    (join (get_attrL 2)
    (arealinterpol
    (getamounts 1)
    (pi2 (get_attrL 2))))
    """
    ,
    """
    1: ObjectInfo(Ratio);     
    join_attr  
    (nest2 (objectfromobjects (pi1 1))  (merge (pi1 (getamounts 1))))
    (nest2 (objectfromobjects (pi1 1)) (avg (getamounts 1))) 
    """,
    """
    1: ObjectInfo(Ratio);
    2: ObjectInfo(Ratio);
    3: ObjectInfo(Ratio);
    4: ObjectInfo(Ratio);
    join_attr
        (get_attrL 1)
        (diversity
            (addlistrel
                (addlistrel
                    (addlistrel            
                        (conslistrel
                            (apply2 ratio 
                                (get_attrR 1)            
                                (apply1 (compose size deify) (get_attrL 1))
                            )
                        )
                        (apply2 ratio 
                                (get_attrR 2)            
                                (apply1 (compose size deify) (get_attrL 2))
                        )
                    )
                    (apply2 ratio 
                                (get_attrR 3)            
                                (apply1 (compose size deify) (get_attrL 3))
                    )
                )
                (apply2 ratio 
                                (get_attrR 4)            
                                (apply1 (compose size deify) (get_attrL 4))
                )    
            )
        )
    """,
    """
    1: ObjectInfo(Nom);        
    join_attr     
    (nIntersections((get_attrL 1), (get_attrL 1)))
    (apply nominalize 
        (pi1 
            (nIntersections((get_attrL 1), (get_attrL 1)))   
        )
    )
    """
    ,
    """
    1:ObjectInfo(Nom);
    2:ObjectInfo(Ratio);
    join_attr (get_attrL 1) (get_attrR 2) 
    """,
    """
    select (compose2 notj leq) (1: ObjectInfo(Ratio)) (-: Ratio)
    """,
    """
        1: ObjectInfo(Nom);
        2: ObjectInfo(Nom);
        subset
            1
            (pi1 (select
                leq
                (oDist (get_attrL 1) (get_attrL 2))
                (-:Ratio)
            ))
    """
    ,
    """
    1: ObjectInfo(Ratio);
    2: Field(Bool);
    arealinterpol
        (getamounts 1)
        (pi2 (groupbyR reify (select eq (loTopo
            (fcover 2 (nest true))
            (get_attrL 1)
        ) in)))
    """
    ,
    """           
    1: Field(Ratio);
    2: ObjectInfo(Nom);
    join_attr
        (get_attrL 2)
        (groupbyR sum (join_key
            (select eq (loTopo (pi1 1) (get_attrL 2)) in)
            1
        ))       
    """
    ,
    """
    1: ObjectInfo(Ratio);
    groupbyL 
        (compose sum (apply2 product (get_attrR 1))) 
        (loDist (-:R1(Loc)) (get_attrL 1))
    """
    ,
    """
    1: ObjectInfo(Nom);
    join_attr((get_attrL 1), (-: R2(Obj,Ratio)))
    """
    ,
    """
    1: Network(Ratio);
    2: ObjectInfo(Nom);
    3: ObjectInfo(Nom);        
           nRoutes (get_attrL 2) (get_attrL 3) 1
    """
    ,
    """
    1: ObjectInfo(Nom);
    nbuild(
        join_attr
            (get_attrL 1)
            (apply1
                (compose size deify)
                (get_attrL 1)
            )
    )
    """
    ,
    """
        1: ObjectInfo(Ratio);
        2: ObjectInfo(Nom);
        join_attr
            (get_attrL 2)
            (join (get_attrL 2) (groupbyR sum (join_key
                (select eq (rTopo
                    (pi2 (get_attrL 1))
                    (pi2 (get_attrL 2))
                ) in)
                (getamounts 1)
            )))
    """
    ,
    """
    1: ObjectInfo(Ratio);
    join_attr
        (get_attrL 1)
        (apply1 (product (-:Ratio)) (get_attrR 1))
    """
    ,
    """
    1: ObjectInfo(Ratio);
    2: ObjectInfo(Ratio);
    3: ObjectInfo(Ratio);
    4: ObjectInfo(Ratio);
    join_attr
        (get_attrL 1)
        (diversity
            (addlistrel
                (addlistrel
                    (addlistrel            
                        (conslistrel
                            (apply2 ratio 
                                (get_attrR 1)            
                                (apply1 (compose size deify) (get_attrL 1))
                            )
                        )
                        (apply2 ratio 
                                (get_attrR 2)            
                                (apply1 (compose size deify) (get_attrL 2))
                        )
                    )
                    (apply2 ratio 
                                (get_attrR 3)            
                                (apply1 (compose size deify) (get_attrL 3))
                    )
                )
                (apply2 ratio 
                                (get_attrR 4)            
                                (apply1 (compose size deify) (get_attrL 4))
                )    
            )
        )
    """
    ,
    """
    1: ObjectInfo(Count);        
    join_attr
        (get_attrL 1)
        (apply2 ratio 
            (get_attrR 1)            
            (apply1 (compose size deify) (get_attrL 1))
        )    
    """
    ,
    """
        1: ObjectInfo(Nom);
        2: ObjectInfo(Nom);
        join_attr
            (get_attrL 2)
            (apply1
                (ocont (get_attrL 1))
                (get_attrL 2)
            )
    """
    ,
    """
    1: ObjectInfo(Nom);        
    join_attr     
    (nIntersections((get_attrL 1), (get_attrL 1)))
    (apply nominalize 
        (pi1 
            (nIntersections((get_attrL 1), (get_attrL 1)))   
        )
    )
    """
    ,
    """
    1: ObjectInfo(Nom);        
    join_attr     
    (groupby merge 
        (groupbyL objectfromobjects 
            (select 
                (compose notj leq) 
                (prod3(apply1 (groupby count) (prod_3(consIntersect ((get_attrL 1), (get_attrL 1)))))) 
                (-:Count)
            )
        )
    )
    (apply nominalize 
        (pi1 
            (groupby merge 
                (groupbyL objectfromobjects 
                    (select 
                        (compose notj leq) 
                        (prod3(apply1 (groupby count) (prod_3(consIntersect ((get_attrL 1), (get_attrL 1)))))) 
                        (-:Count)
                    )
                )
            )   
        )
    )
    """
    ,
    """
        1: ObjectInfo(Count);
        2: ObjectInfo(Ratio);
        join_attr
            (get_attrL 1)
            (apply2 ratio (get_attrR 1) (get_attrR 2))
    """
    ,
    """    
    1: Field(Nom);
    2: ObjectInfo(Nom);
    join_attr
            (get_attrL 2)
            (apply1 
                (compose size pi1) 
                (apply1 
                    (compose (subset (1)) deify) 
                    (get_attrL 2)
                )
            )
    """
    ,
    """
    revert (select eq (invert (1: Field(Nom)): Coverages(Nom)) (-: Nom))
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
            1: ObjectInfo(Ratio);     
                nest2 (merge (pi1 (getamounts 1))) (avg (getamounts 1))         
    """,
    """
            nest2 true (ratio
            (size (fcover (1: Field(Bool)) (nest true)))
            (size (fcover (2: Field(Bool)) (nest true)))
        )
    """
    ,
    """
    apply2 ratio (1: Amounts(Ratio)) (2: Amounts(Ratio))
    """
    ,
    """
            1: ObjectInfo(Count);
        2: ObjectInfo(Count);
        join_attr
            (get_attrL 1)
            (apply2 ratio (get_attrR 1) (get_attrR 2))
    """
    ,
    """
    apply1 (product (size (pi1 (1: Field(Nom))))) (2: R2(Bool, Ratio))
    """,
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