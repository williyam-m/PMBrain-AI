"""
Analytics dashboards API for PMBrain AI.
Aggregates metrics across all modules.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Q, F
from apps.evidence.models import RawEvidence
from apps.insights.models import InsightCluster
from apps.opportunities.models import Opportunity, OpportunityScore, OutcomeMetric
from apps.specs.models import GeneratedArtifact
from apps.ai_agents.models import AgentRun


class DashboardView(APIView):
    """Main dashboard aggregation endpoint."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        project_id = request.query_params.get('project')
        org_ids = request.user.memberships.values_list('organization_id', flat=True)

        filters = {'organization_id__in': org_ids}
        if project_id:
            filters['project_id'] = project_id

        evidence_count = RawEvidence.objects.filter(**filters).count()
        processed = RawEvidence.objects.filter(**filters, is_processed=True).count()
        insights_count = InsightCluster.objects.filter(**filters).count()
        opps_count = Opportunity.objects.filter(**filters).count()
        specs_count = GeneratedArtifact.objects.filter(**filters).count()

        # Top insights by frequency
        top_insights = list(
            InsightCluster.objects.filter(**filters)
            .order_by('-frequency')[:5]
            .values('id', 'title', 'frequency', 'severity', 'trend_direction')
        )

        # Opportunity leaderboard
        top_opps = []
        for opp in Opportunity.objects.filter(**filters)[:10]:
            score = opp.scores.first()
            top_opps.append({
                'id': str(opp.id),
                'title': opp.title,
                'status': opp.status,
                'score': score.total_score if score else 0,
            })
        top_opps.sort(key=lambda x: x['score'], reverse=True)

        # Spec readiness
        specs = GeneratedArtifact.objects.filter(**filters)[:10]
        spec_status = []
        for s in specs:
            spec_status.append({
                'id': str(s.id),
                'title': s.title,
                'status': s.status,
                'readiness': s.readiness_score,
                'version': s.current_version,
            })

        # Pipeline stats
        pipeline = {
            'discovered': Opportunity.objects.filter(**filters, status='discovered').count(),
            'evaluating': Opportunity.objects.filter(**filters, status='evaluating').count(),
            'approved': Opportunity.objects.filter(**filters, status='approved').count(),
            'in_progress': Opportunity.objects.filter(**filters, status='in_progress').count(),
            'shipped': Opportunity.objects.filter(**filters, status='shipped').count(),
        }

        # Agent performance
        agent_runs = AgentRun.objects.filter(**filters)
        avg_duration = agent_runs.filter(
            status='completed'
        ).aggregate(avg=Avg('duration_seconds'))['avg']

        return Response({
            'metrics': {
                'evidence_count': evidence_count,
                'evidence_processed': processed,
                'insights_count': insights_count,
                'opportunities_count': opps_count,
                'specs_count': specs_count,
            },
            'top_insights': top_insights,
            'opportunity_leaderboard': top_opps[:5],
            'spec_status': spec_status,
            'pipeline': pipeline,
            'agent_performance': {
                'total_runs': agent_runs.count(),
                'successful': agent_runs.filter(status='completed').count(),
                'failed': agent_runs.filter(status='failed').count(),
                'avg_duration': round(avg_duration or 0, 2),
            }
        })


class InsightAnalyticsView(APIView):
    """Insight-specific analytics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        project_id = request.query_params.get('project')
        org_ids = request.user.memberships.values_list('organization_id', flat=True)
        filters = {'organization_id__in': org_ids}
        if project_id:
            filters['project_id'] = project_id

        insights = InsightCluster.objects.filter(**filters)

        by_severity = {}
        for item in insights.values('severity').annotate(count=Count('id')):
            by_severity[item['severity']] = item['count']

        by_trend = {}
        for item in insights.values('trend_direction').annotate(count=Count('id')):
            by_trend[item['trend_direction']] = item['count']

        segment_pain = {}
        for insight in insights:
            for seg in (insight.segments_affected or []):
                segment_pain[seg] = segment_pain.get(seg, 0) + 1

        return Response({
            'total': insights.count(),
            'by_severity': by_severity,
            'by_trend': by_trend,
            'segment_pain_distribution': segment_pain,
            'emerging': list(
                insights.filter(trend_direction='rising')
                .order_by('-frequency')[:5]
                .values('id', 'title', 'frequency', 'severity')
            ),
        })


class OpportunityAnalyticsView(APIView):
    """Opportunity pipeline analytics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        project_id = request.query_params.get('project')
        org_ids = request.user.memberships.values_list('organization_id', flat=True)
        filters = {'organization_id__in': org_ids}
        if project_id:
            filters['project_id'] = project_id

        opps = Opportunity.objects.filter(**filters)

        by_status = {}
        for item in opps.values('status').annotate(count=Count('id')):
            by_status[item['status']] = item['count']

        by_segment = {}
        for opp in opps:
            for seg in (opp.affected_segments or []):
                by_segment[seg] = by_segment.get(seg, 0) + 1

        # Impact comparison (predicted vs actual)
        outcomes = OutcomeMetric.objects.filter(
            opportunity__in=opps,
            actual_value__isnull=False
        )
        impact_comparison = []
        for o in outcomes[:10]:
            impact_comparison.append({
                'opportunity': o.opportunity.title,
                'metric': o.metric_type,
                'predicted': o.predicted_value,
                'actual': o.actual_value,
                'accuracy': round(1 - abs(o.predicted_value - o.actual_value) / max(o.predicted_value, 1), 2)
            })

        return Response({
            'total': opps.count(),
            'by_status': by_status,
            'by_segment': by_segment,
            'impact_comparison': impact_comparison,
        })
