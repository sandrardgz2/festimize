package com.festimize.repo;

import com.festimize.domain.Performance;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

/**
 * The questions the insights page asks. Native SQL because every one of them
 * is an aggregate across tables the entities do not usefully relate, and a
 * page of counts should be a handful of queries rather than a loop.
 */
public interface InsightsRepository extends JpaRepository<Performance, Long> {

    /** [sets, of which not your own picks] in this user's plan for this edition. */
    @Query(value = """
            select count(*),
                   count(*) filter (where ua.artist_id is null)
              from plan_item i
              join plan pl on pl.plan_id = i.plan_id
              join fact_performance p on p.performance_id = i.performance_id
              left join user_artist ua on ua.artist_id = p.artist_id and ua.user_id = pl.user_id
             where pl.user_id = :userId and pl.edition_id = :editionId
               and i.item_type = 'SET'
            """, nativeQuery = true)
    List<Object[]> discovery(@Param("userId") Long userId, @Param("editionId") Long editionId);

    /** [artists on the bill, of which we hold tags for] — what we could rate. */
    @Query(value = """
            select count(distinct p.artist_id),
                   count(distinct p.artist_id) filter (
                       where exists (select 1 from artist_tag t where t.artist_id = p.artist_id))
              from fact_performance p
             where p.edition_id = :editionId
            """, nativeQuery = true)
    List<Object[]> coverage(@Param("editionId") Long editionId);

    /** [day, minutes of music] for each day of this plan. */
    @Query(value = """
            select date(i.starts_at) as day,
                   sum(extract(epoch from (i.ends_at - i.starts_at)) / 60)::int as minutes
              from plan_item i
              join plan pl on pl.plan_id = i.plan_id
             where pl.user_id = :userId and pl.edition_id = :editionId
               and i.item_type = 'SET'
             group by 1 order by 1
            """, nativeQuery = true)
    List<Object[]> effortByDay(@Param("userId") Long userId, @Param("editionId") Long editionId);

    /**
     * [tag, share of your saved artists, share of this lineup] for the tags
     * that matter to either side. Shares rather than counts: a lineup of 48
     * and a taste of 8 cannot be compared any other way.
     */
    @Query(value = """
            with mine as (
                select t.tag, count(*)::numeric as n
                  from user_artist ua join artist_tag t on t.artist_id = ua.artist_id
                 where ua.user_id = :userId group by 1),
            bill as (
                select t.tag, count(distinct p.artist_id)::numeric as n
                  from fact_performance p join artist_tag t on t.artist_id = p.artist_id
                 where p.edition_id = :editionId group by 1),
            totals as (select (select coalesce(sum(n),1) from mine) as m,
                              (select coalesce(sum(n),1) from bill) as b),
            -- Ranked from both ends. Ordering by your own counts alone fills
            -- every row with tags you already have, and the panel exists to
            -- show the opposite: the parts of a bill your profile is silent
            -- about. A tag qualifies if it is big for you OR big here.
            paired as (
                select coalesce(mine.tag, bill.tag) as tag,
                       coalesce(mine.n, 0) / totals.m as you,
                       coalesce(bill.n, 0) / totals.b as lineup
                  from mine full outer join bill on bill.tag = mine.tag, totals)
            select tag, round(you * 100, 1), round(lineup * 100, 1)
              from paired
             where tag in (select tag from paired order by you desc limit 6)
                or tag in (select tag from paired order by lineup desc limit 6)
             order by greatest(you, lineup) desc
            """, nativeQuery = true)
    List<Object[]> tasteAgainstLineup(@Param("userId") Long userId,
                                      @Param("editionId") Long editionId);

    /** Artists the measure calls rising who are on this bill and not yours. */
    @Query(value = """
            select a.artist_id, a.name,
                   round(coalesce(sc.match_score, 0) * 100)::int as match,
                   p.starts_at as slot,
                   coalesce(s.name, '') as stage,
                   p.performance_id
              from fact_performance p
              join dim_artist a on a.artist_id = p.artist_id
              join artist_momentum m on m.artist_id = a.artist_id
              left join dim_stage s on s.stage_id = p.stage_id
              left join artist_score sc on sc.artist_id = a.artist_id and sc.user_id = :userId
             where p.edition_id = :editionId
               and m.basis = 'trajectory' and m.festivals >= 3 and m.momentum_score >= 0.75
               and not exists (select 1 from user_artist ua
                                where ua.user_id = :userId and ua.artist_id = a.artist_id)
             order by coalesce(sc.match_score, 0) desc, p.starts_at
             limit 8
            """, nativeQuery = true)
    List<Object[]> risingNotYours(@Param("userId") Long userId,
                                  @Param("editionId") Long editionId);
}
