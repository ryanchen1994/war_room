SELECT r.*
FROM [PT].[dbo].[Remar] r
WHERE r.COP_NO IN ('HG','HM')
  AND r.PROJM_NO IN ('0027-1', '0040', '0051', '0021', '0038')
  AND r.DAY_DATE = (
      SELECT MAX(r2.DAY_DATE)
      FROM [PT].[dbo].[Remar] r2
      WHERE r2.PROJM_NO = r.PROJM_NO
        AND r2.COP_NO IN ('HG','HM')
  )
ORDER BY r.PROJM_NO ASC;  -- 加入排序