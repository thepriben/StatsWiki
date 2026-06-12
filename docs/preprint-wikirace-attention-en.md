# From Events to Encyclopedic Attention
## A Cautious Pipeline for Perimeter Design, Wikidata Reverse Expansion, and Pageview-Based Audit

**Benoît Prieur** · ORCID [0000-0003-0786-0049](https://orcid.org/0000-0003-0786-0049) · Independent researcher

> **Preprint v2 (June 2026)** — Corrects Ballon d'Or 2025 Vitinha pageviews and Race% in [Zenodo v1](https://doi.org/10.5281/zenodo.20635352). Export to PDF for deposit.

## Abstract

Daily English Wikipedia pageviews offer a public and reproducible trace of article access, used here as a weak proxy for encyclopedic attention.

This paper presents a methodological pipeline for moving from an event to a closed group of Wikipedia articles, from that group to a time-windowed pageview distribution, and from the observed distribution to a semantic and editorial audit.

The operational index, Race%, is defined as the share of cumulative group views received by an article:

the discrete area under its daily pageview curve divided by the total area for the group.

The contribution lies in the pipeline rather than in a universal ranking metric. The method combines forward perimeter design, pageview aggregation, Wikidata-based reverse expansion, leak auditing, and retro-pedagogical interpretation.

A small set of cases in sport, mathematics, television culture, artificial intelligence, software infrastructure, and politics illustrates how the approach can be applied across heterogeneous domains.

Numerical claims are deliberately limited to audited data or to values explicitly labeled as provisional.

The Gus Fring case, involving a character shared by Breaking Bad and Better Call Saul, is used as a minimal attribution framework for non-bijective relations between events and article traffic.

The paper closes by discussing benefits, limitations, reproducibility requirements, and possible encyclopedic interventions, including hubs, redirects, cross-links, and re-measurement.

**Keywords:** Wikipedia; pageviews; attention; Wikidata; knowledge graph; event window; digital methods; open science; encyclopedic design.

## Version and data note

Earlier exploratory tables used all-agents pageviews. This version treats all-access/user as the default for claims about attention.

Legacy all-agents values should not be cited as evidence of human consultation unless clearly labeled.

Two numerical cases have been rerun in this draft from Wikimedia Pageviews API data:

the 2025 Ballon d'Or week-before case and the October 2019 sum-of-three-cubes case.

Other cases are retained as conceptual or qualitative examples unless a user-only export is archived. For the Ballon d'Or rerun, pageviews were queried on the enwiki sitelink title **Vitinha** (Q66818509). Zenodo v1 mistakenly used the path *Vitinha (footballer, born February 2000)*, which aggregates a different pageview series.

## 1. Introduction Wikipedia pageviews are a weak but useful signal. They do not reveal why a page was opened, whether it was read carefully, what the reader already knew, or whether the consultation reflected expertise, fandom, school work, media exposure, professional interest, or incidental curiosity.

They also do not identify unique readers in the data used here.

They nevertheless constitute a public, timestamped, and re-runnable trace of article access.

When aggregated over a calibrated window, they can help observe which articles become entry points into an event.

The starting problem is comparative. Many analyses of Wikipedia attention focus on a single article:

a peak after a death, release, election, scientific announcement, sporting final, or cultural controversy.

That approach is useful, but it does not answer a closed-group question:

within a specific event, how is attention distributed among relevant entities?

For a prize ceremony, should one compare the winner with finalists?

For a mathematical result, should one include the mathematician, the theorem, the number, and surrounding concepts?

For a software release, should one compare the new feature, the platform that absorbs it, and the incumbent stack that readers already know?

The pipeline studied here answers this comparative question by constructing a closed group of articles and calculating each article's share of cumulative group views.

The tool used to instantiate the method is Wikirace, a browser-based prototype in the StatsWiki project.

The paper is deliberately centered less on the tool name than on the method:

how one moves from an event to a perimeter, from a perimeter to a pageview distribution, from a distribution to an audit, and from the audit to possible encyclopedic interventions.

The central formula is simple: Race% equals area under the curve within a closed group. It is an encyclopedic attention index, not a vote, not a prediction, and not a measure of reader expertise.

The formula is useful because it forces interpretation.

A player can win a trophy and lose the attention race.

A mathematical concept can be central to a result and marginal in public consultation.

A general article can absorb attention that the event-specific article receives only weakly.

Such outcomes are not failures of the index; they are the phenomena the pipeline is designed to make visible.

Five questions organize the paper. What exactly does a pageview-share index measure?

When and why does the official outcome of an event fail to dominate encyclopedic attention?

Can Wikidata reverse expansion help construct or audit a perimeter?

How can non-bijective attribution between event and article traffic be formalized without overstating causality?

How can post-hoc measurement support a retro-pedagogical loop:

measure, detect surprise, explain the gap, propose an encyclopedic intervention, and re-measure?

2. Related Work and Positioning This paper sits at the intersection of Wikipedia pageview analysis, Wikidata and knowledge graphs, and digital-methods pedagogy.

Wikipedia pageviews have been used to examine public attention around current events, cultural phenomena, political cycles, health concerns, and scientific communication.

Their value is accessibility and temporal resolution.

Their limits

are equally important: language effects, media effects, bot filtering, lack of reader demographics, and the impossibility of directly inferring intent.

Wikidata adds a structured semantic layer to the Wikimedia ecosystem. Entities are identified by QIDs and connected through properties such as award received, point in time, field of work, notable work, software version, programmed in, uses, and present in work.

This structure enables candidate generation through SPARQL.

In this pipeline, Wikidata has two functions.

It stabilizes article identity through QIDs, and it supports reverse expansion:

instead of manually selecting all articles, the analyst starts from an event entity and asks which related entities might form a defensible perimeter.

The methodological gap is that pageview analysis and knowledge-graph expansion are often treated separately.

Pageviews say what was accessed; Wikidata says how entities are semantically related.

The pipeline proposed here compares these two layers.

A Wikidata perimeter is a semantic hypothesis.

A pageview distribution is an empirical trace of consultations.

The difference between them is analytically productive, especially when readers enter through hubs, redirects, celebrity pages, cultural numbers, or absent event articles.

The paper therefore avoids two symmetric errors. It does not claim that pageviews are a pure proxy for public opinion, importance, expertise, or outcome.

It also does not claim that a semantic graph can predict reading behavior.

Instead, both are treated as partial instruments.

Wikidata helps produce and audit candidate perimeters; pageviews reveal the distribution of consultations inside the chosen group.

3. Data, Index, and Pipeline 3.1 Data source and implementation constraints The pipeline uses daily pageviews for English Wikipedia articles through the Wikimedia Pageviews API.

The query pattern is per-article, project en.wikipedia, all-access, user, daily granularity, with a start and end date.

The Pageviews API also permits other agent filters; the methodological default for this manuscript is user rather than all-agents.

This matters because the paper interprets pageviews as a weak proxy for human attention.

If all-agents values are used in future comparisons, they should be labeled as such and compared against user-only results.

The Pageviews API data begin on 2015-07-01. The prototype runs in the browser rather than from a StatsWiki server-side pageview store.

A race is encoded by a URL containing QIDs and dates, for example:

https://statswiki.info/wikirace/{QID1}+{QID2}+.../{YYYY-MM-DD}/{YYYY-MM-DD}.

The current implementation imposes a maximum of ten articles and a maximum span of 365 days.

These constraints are not merely technical; they discipline the comparison by keeping the perimeter small enough to be audited and the window narrow enough to discuss.

3.2 Race% as a closed-group attention share

Let G = {Q1, ..., Qn} be a closed group of Wikidata entities with English Wikipedia sitelinks.

Let W = [t0,t1] be a discrete window of days.

Let v_Q(t) be the pageviews of article Q on day t.

The cumulative volume is V(Q,W) = sum_{t in W} v_Q(t).

The attention share is:

Race%(Q | G,W) = V(Q,W) / sum_{Q' in G} V(Q',W) x 100 This is the discrete area under the pageview curve. In a stacked-share visualization, the colored surface occupied by an article corresponds to its Race%.

In a daily comparison chart, the same data reveal peaks and temporal dynamics.

The aggregate and daily views answer different questions:

how much of the total attention did an article receive, and when did that attention occur?

3.3 Event windows Window type Rule Typical use Before End date is the day before the event Elections, award ceremonies, finals After Start date is the day after the event Launches, releases, announcements During Window includes the event day Opening weeks, concurrent cultural events Rolling Window is recalculated up to yesterday Ongoing political or cultural attention Window design is part of the method. A before window measures anticipatory attention. An after window measures reception.

A during window captures simultaneous cultural activity.

A rolling window measures ongoing attention without a single event date.

Interpretation should change with the window:

a week-before award window is not a prediction machine, and a rolling political window is not an event-attribution design.

3.4 Forward perimeter design Forward design means that the analyst manually chooses the group before measuring. This choice must be documented.

Each preset should specify the event date where relevant, the window, the interpretive context, and the rationale for inclusion and exclusion.

The perimeter should be closed and analytically defensible.

It should avoid mixing different narrative contexts, and it should flag articles whose traffic is plausibly dominated by unrelated attention.

Several exclusions are canonical. Gus Fring should not be included in a Breaking Bad anniversary preset because the character is also central to Better Call Saul.

Bitcoin should not be inserted into a narrowly defined Ethereum Merge preset because it would import broad cryptocurrency traffic.

Large language model should not be retroactively used in December 2022 without checking whether the relevant English Wikipedia article existed and functioned as such at that time; Language model is the documented substitute in the current preset.

Sum_of_three_cubes is a redirect, so the relevant technical article is Sums_of_three_cubes.

3.5 Reverse Wikidata expansion Reverse expansion starts from the event and derives candidate articles through Wikidata.

The procedure is:

choose an event anchor, expand with SPARQL over one or two hops, filter for English Wikipedia sitelinks, audit bijectivity, retain up to ten candidates, run the pageview comparison, and compare the result with the forward perimeter.

Properties useful for this

process include P166 (award received), P585 (point in time), P1344 (participant in), P1441 (present in work), P800 (notable work), P101 (field of work), P348 (software version), P277 (programmed in), P2283 (uses), P577 (publication date), and P50 (author).

Reverse expansion does not solve the perimeter problem. It makes the problem auditable.

Wikidata can reveal that an entity is semantically connected to an event; it cannot by itself determine whether the article's traffic during the window is attributable to that event.

That distinction motivates the attribution framework below.

4. Non-Bijective Attribution: A Minimal Framework Events and articles are not in one-to-one correspondence. An event may lead users to many articles, and an article may receive traffic from several unrelated contexts.

Gus Fring provides a clean cultural example.

The same encyclopedic entity is present in Breaking Bad and Better Call Saul.

If the window is designed around the tenth anniversary of the Breaking Bad finale, Gus Fring traffic cannot be cleanly attributed to that anniversary.

It may reflect Better Call Saul, the actor, fandom memory, memes, or general character interest.

The framework is conceptual rather than estimative. For an article Q and window W, the observed volume can be decomposed as V(Q,W) = V_E(Q,W) + V_not_E(Q,W).

The first term is the volume attributable to event E; the second term groups leaks:

other events, background traffic, general hubs, celebrity interest, redirects, and missing hub articles.

A latent attribution score could be written alpha(Q,E,W) = V_E(Q,W) / V(Q,W).

Strong event bijectivity corresponds to alpha close to 1.

A Gus-Fring-like case corresponds to alpha much lower than 1.

The paper does not claim that alpha is identifiable from pageviews alone. Without counterfactual or experimental control, V_E cannot be directly measured.

The use of the decomposition is diagnostic:

it names structural risk factors that make low attribution plausible.

Those risk factors include multi-work narrative membership, high baseline traffic, high hub generality, absent or redirected article titles, celebrity power, and incumbent technical stacks.

Type Code Mechanism Example Multi-context narrative T1 One entity belongs to several narrative contexts Gus Fring Generalist hub T2 A broad concept absorbs event attention Modular arithmetic Baseline or pop culture T3 High background traffic unrelated to the event 42 (number) Absent article or redirect T4 Attention cannot concentrate on the specific object Sum_of_three_cubes Media star power T5 Celebrity traffic exceeds outcome relevance Donnarumma Incumbent stack T6 Users enter through established infrastructure C, C++, Linux This taxonomy is useful only if used modestly. It does not prove causes; it structures interpretation.

In mathematics, 42 (number) is a Gus Fring analogue not because it belongs to two television series, but because it is a multi-interpretive sign:

a number, a cultural

reference, a meme, and a mathematical object. In software infrastructure, the absence of an event-specific hub can push attention toward Linux, C, C++, or memory safety.

In sport, a player can receive attention because of media salience rather than award outcome.

5. Audited Case Studies 5.1 Award attention and outcome divergence: Ballon d'Or 2025 The 2025 men's Ballon d'Or provides the strongest audited example of divergence between institutional outcome and encyclopedic attention.

The preset compares ten finalists over the week before the ceremony, from 2025-09-15 to 2025-09-21, using all-access/user pageviews.

The official winner is Ousmane Dembélé, with Lamine Yamal second and Vitinha third.

In the pageview race, Dembélé ranks seventh and Vitinha ranks tenth (last in the group), with only 64 user pageviews (<0.1% of the group total).

Gianluigi Donnarumma, ninth in the official ranking, receives the largest attention share.

| Race rank | Article | User views | Race% | Official rank |
|---:|---|---:|---:|---:|
| 1 | Gianluigi Donnarumma | 110,665 | 24.3% | 9 |
| 2 | Kylian Mbappé | 92,055 | 20.2% | 7 |
| 3 | Lamine Yamal | 80,081 | 17.6% | 2 |
| 4 | Mohamed Salah | 61,330 | 13.5% | 4 |
| 5 | Cole Palmer | 42,617 | 9.4% | 8 |
| 6 | Raphinha | 31,596 | 6.9% | 5 |
| 7 | Ousmane Dembélé | 19,862 | 4.4% | 1 |
| 8 | Achraf Hakimi | 10,507 | 2.3% | 6 |
| 9 | Nuno Mendes | 6,639 | 1.5% | 10 |
| 10 | Vitinha | 64 | <0.1% | 3 |

The group total is **455,416** user pageviews. The result should not be interpreted as a prediction failure because the index is not predictive.

It shows that attention in the week before the ceremony followed media visibility, celebrity trajectories, and independent curiosity rather than the final jury ranking.

The interpretation as T5, media star power, is plausible but should remain phrased as an interpretation rather than a causal claim.

The key empirical statement is narrower and stronger:

in this closed group and window, the official winner did not dominate Wikipedia attention.

5.2 Mathematics as public attention: 42 and sums of three cubes The October 2019 case around the representation of 42 as a sum of three cubes demonstrates how a specific mathematical result can be overshadowed by general and cultural entry points.

The audited user-only monthly totals for October 2019 are below.

Unlike the earlier exploratory table, this version does not claim that Sums of three cubes received only negligible traffic; it received 6,109 user views, still far below the general hubs but no

longer close to zero. This correction strengthens the paper by separating a real effect from an exaggerated one.

| Race rank | Article | User views | Race% |
|---:|---|---:|---:|
| 1 | Modular arithmetic | 50,939 | 33.9% |
| 2 | 42 (number) | 38,025 | 25.3% |
| 3 | Number theory | 31,061 | 20.7% |
| 4 | Diophantine equation | 17,014 | 11.3% |
| 5 | 33 (number) | 6,875 | 4.6% |
| 6 | Sums of three cubes | 6,109 | 4.1% |
| 7 | Andrew Booker | 64 | 0.0% |

The group total is **150,087** user pageviews. Modular arithmetic, 42 (number), and Number theory together account for about 80%

of the group attention.

The technical article Sums of three cubes receives 4.1%, which is not zero, but it remains much less visible than the schoolbook and cultural entry points.

A control value reinforces the baseline issue:

42 (number) received 123,597 user pageviews in June 2019, a month not centered on the Booker-Sutherland announcement.

This supports a T3 reading, with 42 functioning as a high-baseline cultural article.

5.3 Scientific prestige and technical objects: Fields Medal 2022 The Fields Medal 2022 case is retained as a conceptual example but should not be treated as a fully audited numerical result in this draft.

The dossier suggests that the medal page and laureate pages dominate technical objects such as E8 lattice, Leech lattice, Kissing number, Modular form, and Sphere packing.

That pattern is plausible and substantively interesting, but a submission version should include a user-only daily export for 2022-07-06 to 2022-08-05 before making exact Race%

claims.

In the meantime, the safe conclusion is qualitative:

Wikidata can identify laureates, fields, and related concepts, but readers may enter through prize and biography pages rather than technical structures.

5.4 Software infrastructure: Rust in Linux 6.1 The Rust in Linux 6.1 case illustrates the possibility that a technical event lacks a stable event-specific encyclopedic entry point.

Linux 6.1 was released on 2022-12-11 and included initial support for the Rust programming language.

The careful claim is historical and perimeter-specific:

the analyzed preset did not provide a dedicated Rust-in-Linux-6.1 hub, and the state of English Wikipedia in December 2022 should be audited before making stronger claims.

The case is therefore used as a T6 example of possible leakage toward incumbent infrastructure:

Linux, C, C++, Rust, and memory safety.

This is not evidence that the event was unimportant. It is evidence that navigational structure matters.

A retro-pedagogical intervention could include a dedicated section or article on Rust for Linux, redirects from plausible search strings, and cross-links from Linux kernel, Rust, C, C++, and memory safety.

The measurement becomes a diagnostic of navigability rather than a ranking of technical importance.

5.5 ChatGPT and historically available articles

The ChatGPT launch preset covers the month after 2022-11-30. The perimeter includes ChatGPT, OpenAI, Artificial intelligence, Machine learning, Language model, and related entries.

The methodological point is historical availability.

A present-day analyst may be tempted to use Large language model as the obvious conceptual hub, but a historically responsible analysis must verify the state of the English Wikipedia article at the time of the event.

The current preset uses Language model as the documented substitute.

A submission version should cite the relevant page history, creation log, or redirect history for Large language model.

5.6 Television culture and clean perimeters Breaking Bad and Better Call Saul provide a controlled example of T1, multi-context narrative leakage.

Gus Fring, Saul Goodman, and Mike Ehrmantraut are not simply relevant entities.

They are shared entities.

Including them in a single-work anniversary preset would create a mixed signal.

The clean forward solution is to exclude shared characters from presets centered on one series, unless the explicit goal is to stress-test contamination.

This decision is methodological, not editorial:

it protects the interpretation of the window.

5.7 Rolling political attention The French politics preset uses a rolling twelve-month window rather than a single event date.

It compares attention across a set of political figures through yesterday.

Its purpose is not to detect a winner, predict an election, or attribute traffic to a specific campaign event.

It captures ongoing attention.

The rolling case clarifies that the pipeline is not limited to discrete events, but the interpretation changes:

without an event anchor, reverse expansion and causal attribution must be used more cautiously.

6. Benefits of the Pipeline The first benefit is interpretive discipline. Because the group is closed, the analyst must name the comparison space.

Because the window is explicit, the analyst must say whether the measured attention is anticipatory, contemporaneous, retrospective, or rolling.

Because the index is a share, the analyst sees attention distribution rather than isolated peaks.

The second benefit is reproducibility in a qualified sense. A race can be rerun from public endpoints when the QIDs, article titles, dates, access type, agent filter, redirect policy, extraction date, and code version are known.

This is stronger than an anecdotal screenshot, but weaker than archival reproducibility unless the raw JSON or CSV exports are stored.

The manuscript should therefore distinguish re-runnable from archived.

The third benefit is semantic auditability. Wikidata reverse expansion does not replace judgment, but it provides a principled way to ask what the perimeter could have been.

The forward group and reverse group can be compared by overlap, missing candidates, semantic leaks, and rank disagreement.

This helps reveal whether the manual perimeter is too narrow, too broad, or contaminated by ambiguous entities.

The fourth benefit is pedagogical. Counter-intuitive results are useful. When Dembélé wins the Ballon d'Or but not the pageview race, students can discuss attention versus outcome.

When 42 and modular arithmetic dominate the sum-of-three-cubes event, they can discuss cultural baseline and hubs.

When C and Linux dominate a Rust-in-Linux narrative, they can discuss missing articles and incumbent infrastructure.

The method turns surprises into lessons about data interpretation.

The fifth benefit is encyclopedic diagnosis. Low attention to a technical article may reveal an inaccessible lead, weak linking from hubs, poor redirects, or the absence of a transversal article.

High attention to a general article may reveal where users actually enter a topic.

The method does not prescribe what Wikipedia should say, but it can indicate where navigational scaffolding may be weak.

7. Limits and Risks · Language: the cases use English Wikipedia. Other language editions require separate perimeters, article-availability checks, and cultural interpretation.

· Population opacity: pageviews do not include public fine-grained reader identity, demographic profile, expertise, motivation, or reading depth.

· Agent filtering: attention claims should use the user agent filter. All-agents values may be useful for robustness checks but should not be silently treated as human attention.

· Causal non-identifiability: observed traffic can be compatible with an event without being caused by it.

The attribution decomposition is conceptual, not directly estimated.

· Perimeter sensitivity: Race% changes when the group changes. This is a warning against universalizing any single race, not a reason to discard the method.

· Article history: Wikipedia articles are created, renamed, redirected, merged, split, or improved.

Historical analyses must respect the article graph at the time of the event.

· Strategic misuse: a pageview-share index should not encourage traffic gaming, fan mobilization, or claims that high attention warrants greater encyclopedic importance.

8. Retro-Pedagogy and Encyclopedic Interventions Retro-pedagogy is the post-hoc use of the pipeline after an event is known. It has five steps:

select a known event, build a forward preset, calculate Race%, identify a surprise, explain the surprise with the leak taxonomy, and propose an intervention.

Re-measurement can occur later or on an analogous event.

Observed pattern Likely diagnosis Possible intervention Technical article receives little attention Weak access path or specialized title Improve lead; link from hubs; add contextual section General hub dominates Users enter through broad concept Add cross-link from hub to event-specific article Cultural number dominates High baseline and pop-cultural reading Clarify recent-result links and disambiguation

Shared character dominates Multi-work contamination Use separate perimeters; add hatnotes if useful Incumbent stack dominates No event-specific hub Create or improve transversal article or section Award winner loses attention race Outcome differs from media attention Teach attention versus institutional decision This approach is suited to classroom and workshop settings. In a data literacy exercise, students can be asked to predict the attention distribution before seeing the result, then diagnose the difference.

In a digital humanities seminar, they can compare forward and reverse perimeters.

In a Wikipedia workshop, they can inspect how redirects, leads, and cross-links structure actual reading paths.

The purpose is not to turn pageviews into editorial authority, but to make public attention legible and contestable.

9. Reproducibility Protocol A submission-ready version should archive, for every numerical case, the following elements:

QID list, resolved English Wikipedia titles, start and end dates, access parameter, agent parameter, redirect policy, extraction date, raw JSON or CSV export, code version, and any errors or missing sitelinks.

The recommended default is all-access/user.

A minimal API request has the following form:

https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{ ARTICLE}/daily/{START}/{END} For monthly control windows, monthly granularity can be used, but it should not be silently mixed with daily windows if the paper claims exact comparability.

The current draft uses daily user data for Ballon d'Or 2025 and monthly user data for October 2019 in the sum-of-three-cubes case.

10. Conclusion The pipeline described in this paper converts Wikipedia pageviews into a closed-group attention share over a calibrated window.

Its core index is intentionally simple:

Race%

is the area under the curve for one article divided by the total area under the curves for the group.

Its interpretation is intentionally restricted:

it is an index of encyclopedic attention, not a vote, not a prediction, and not a measure of reader expertise.

The contribution is the combination of forward design, reverse Wikidata expansion, a cautious non-bijectivity framework, and retro-pedagogical use.

The forward step makes the comparison explicit.

The reverse step audits it semantically.

The attribution framework explains why articles may receive attention from other contexts.

The pedagogical loop transforms surprising results into analyses of how users navigate an encyclopedia.

The empirical cases show that the official outcome of an event and the attention distribution around it can diverge sharply.

Dembélé can win the Ballon d'Or while Donnarumma wins the pageview race.

A mathematical announcement about 42 can send users mainly to 42 (number), modular arithmetic, and number theory rather than to the technical article.

A software milestone can be absorbed by incumbent infrastructure when the event lacks a

stable hub. These divergences are not anomalies; they are evidence that encyclopedic attention often follows entry points, not only semantic proximity.

The broader lesson is methodological humility. Pageviews are not meaning, but they are traces.

Wikidata is not reading behavior, but it is a structured hypothesis space.

Together, they support a practical audit pipeline for public, re-runnable, and critically interpretable studies of encyclopedic attention.

## Appendix A. Core Data Rerun

The following data were rerun for this revision under all-access/user. See [`preprint-wikirace-audit-data.csv`](preprint-wikirace-audit-data.csv) for the full export.

| Case | Window | Access / agent | Group total | Status |
|---|---|---|---:|---|
| Ballon d'Or 2025 | 2025-09-15 to 2025-09-21 | all-access / user | 455,416 | daily export audited |
| Sum of three cubes | 2019-10 monthly | all-access / user | 150,087 | monthly export audited |
| 42 baseline control | 2019-06 monthly | all-access / user | 123,597 | single-article baseline |
| Fields Medal 2022 | 2022-07-06 to 2022-08-05 | all-access / user | — | pending; do not cite exact Race% yet |
| Rust in Linux 6.1 | 2022-12-12 to 2023-01-11 | all-access / user | — | qualitative only in this draft | Appendix B. SPARQL Templates Fields Medal 2022 laureates with English Wikipedia article SELECT ?person ?personLabel ?article WHERE { ?person p:P166 ?stmt .

?stmt ps:P166 wd:Q28835 ; pq:P585 ?date .

FILTER(YEAR(?date) = 2022) ?article schema:about ?person ; schema:isPartOf <https://en.wikipedia.org/> .

SERVICE wikibase:label { bd:serviceParam wikibase:language "en".

} } Gus Fring narrative ambiguity SELECT ?character ?characterLabel ?work ?workLabel WHERE { wd:Q23369 wdt:P1441 ?work .

?character wdt:P1441 ?work .

SERVICE wikibase:label { bd:serviceParam wikibase:language "en".

} }

Appendix C. Preset Catalogue Status Area Preset Window Status in this draft Politics 2024 US Presidential Election 2024-05-09 to 2024-11-04 listed; not numerically analyzed Politics 2020 US Presidential Election 2020-05-07 to 2020-11-02 listed; not numerically analyzed Politics 2016 US Presidential Election 2016-05-12 to 2016-11-07 listed; not numerically analyzed Politics France politics rolling rolling one year conceptual rolling example Sport Men's Ballon d'Or 2025 2025-09-15 to 2025-09-21 user-only audited Sport Women's Vélo d'Or 2025 2025-11-28 to 2025-12-04 to measure Culture Barbenheimer 2023-07-21 to 2023-07-27 listed; not numerically analyzed Culture Breaking Bad / Better Call Saul post-finale windows T1 perimeter example Science/Tech ChatGPT launch 2022-12-01 to 2022-12-31 conceptual; article history to verify Science/Tech Rust in Linux 6.1 2022-12-12 to 2023-01-11 qualitative; user export pending Science/Tech Sum of three cubes 2019-10 user-only audited Science/Tech Fields Medal 2022 2022-07-06 to 2022-08-05 qualitative; user export pending References and Source Notes 1.

Wikimedia Foundation. Wikimedia Analytics API, Pageviews / page metrics documentation.

https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/ 2.

Wikimedia Foundation. Pageviews Analysis tools. https://pageviews.wmcloud.org/ and https://meta.wikimedia.org/wiki/Pageviews_Analysis 3.

Wikidata. SPARQL Query Service.

https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service 4.

MediaWiki. Wikidata Query Service User Manual.

https://www.mediawiki.org/wiki/Wikidata_query_service/User_Manual 5.

StatsWiki / Wikirace. Project source: https://github.com/thepriben/StatsWiki, tag v0.35; live tool:

https://statswiki.info/wikirace.

6.

UEFA. 2025 Ballon d'Or voting results: official rankings.

https://www.uefa.com/uefachampionsleague/news/029e-1eeae3a29e5c-64e217276491- 1000--2025-ballon-d-or-voting-results-official-rankings/ 7.

OpenAI. Introducing ChatGPT, 2022-11-30. https://openai.com/index/chatgpt/ 8.

Linux Kernel Newbies. Linux 6.1 release summary.

https://kernelnewbies.org/Linux_6.1 9.

Linux Kernel documentation. Rust support in the kernel.

https://www.kernel.org/doc/html/latest/rust/ 10.

International Mathematical Union. Fields Medals 2022.

https://www.mathunion.org/imu-awards/fields-medal/fields-medals-2022 11.

University of Bristol. Sum of three cubes for 42 finally solved, 2019-09-06.

https://www.bristol.ac.uk/news/2019/september/sum-of-three-cubes-.html

12.

MIT News. The answer to life, the universe, and everything, 2019-09-10.

https://news.mit.edu/2019/answer-life-universe-and-everything-sum-three-cubes-mathematics-0910
