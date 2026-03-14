"""
Seed demo data for PMBrain AI.
Creates a complete demo environment with realistic product data.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User
from apps.organizations.models import Organization, OrgMembership
from apps.projects.models import Project
from apps.datasources.models import DataSource
from apps.evidence.models import RawEvidence
from apps.insights.models import InsightCluster
from apps.opportunities.models import Opportunity, OpportunityScore
from apps.specs.models import GeneratedArtifact, ArtifactVersion
from apps.notifications.models import Notification


class Command(BaseCommand):
    help = 'Seed PMBrain AI with demo data'

    def handle(self, *args, **options):
        self.stdout.write('🧠 Seeding PMBrain AI demo data...\n')

        # Create demo user
        user, created = User.objects.get_or_create(
            email='demo@pmbrain.ai',
            defaults={
                'username': 'demo',
                'full_name': 'Alex Chen',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            user.set_password('demo1234')
            user.save()
            self.stdout.write(self.style.SUCCESS('  ✓ Demo user created (demo@pmbrain.ai / demo1234)'))
        else:
            self.stdout.write('  → Demo user already exists')

        # Create second user
        user2, _ = User.objects.get_or_create(
            email='sarah@pmbrain.ai',
            defaults={
                'username': 'sarah',
                'full_name': 'Sarah Kim',
            }
        )
        if _:
            user2.set_password('demo1234')
            user2.save()

        # Create organization
        org, created = Organization.objects.get_or_create(
            slug='acme-saas',
            defaults={
                'name': 'Acme SaaS',
                'description': 'B2B SaaS platform for project management',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Organization created'))

        # Memberships
        OrgMembership.objects.get_or_create(
            organization=org, user=user,
            defaults={'role': 'org-owner'}
        )
        OrgMembership.objects.get_or_create(
            organization=org, user=user2,
            defaults={'role': 'product-manager'}
        )

        # Create project
        project, created = Project.objects.get_or_create(
            organization=org, slug='acme-crm',
            defaults={
                'name': 'Acme CRM',
                'description': 'Customer relationship management platform',
                'product_context': 'Acme CRM is a B2B SaaS CRM tool used by 2,400 companies. Primary segments: Enterprise (40% ARR), Mid-Market (35%), SMB (25%). Key value prop: unified customer data + workflow automation. Main competitors: Salesforce, HubSpot.',
                'goals': [
                    'Reduce enterprise churn by 20% this quarter',
                    'Increase activation rate for new signups to 60%',
                    'Launch 3 features driven by customer feedback',
                    'Expand into healthcare vertical'
                ],
                'scoring_weights': {
                    'frequency': 0.25,
                    'revenue': 0.25,
                    'retention': 0.20,
                    'alignment': 0.15,
                    'effort': 0.15,
                },
                'created_by': user,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Project created'))

        # Data Sources
        sources_data = [
            ('Zendesk Support', 'support_ticket', 'Customer support tickets from Zendesk'),
            ('User Interviews Q3', 'interview_transcript', 'Quarterly user interview program'),
            ('Product Board', 'feature_request', 'Feature requests from Product Board'),
            ('NPS Survey Aug', 'nps_survey', 'August NPS survey responses'),
            ('Exit Interviews', 'churn_feedback', 'Customer exit interview transcripts'),
            ('Slack Community', 'slack_thread', 'Customer Slack community threads'),
        ]
        sources = {}
        for name, stype, desc in sources_data:
            ds, _ = DataSource.objects.get_or_create(
                organization=org, project=project, name=name,
                defaults={'source_type': stype, 'description': desc, 'created_by': user}
            )
            sources[stype] = ds

        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(sources_data)} data sources created'))

        # Evidence Items
        evidence_data = [
            {
                'evidence_type': 'support_ticket',
                'title': 'Export fails on large datasets',
                'text': 'We have over 50,000 contacts and every time I try to export them, the export just hangs and eventually times out. This has been happening for 3 weeks now. We need this data for our quarterly board report. This is blocking our entire analytics workflow.',
                'customer_segment': 'enterprise',
                'source_name': 'zendesk',
                'sentiment': 'negative',
                'urgency': 9,
            },
            {
                'evidence_type': 'support_ticket',
                'title': 'No way to schedule automated reports',
                'text': 'I spend 3 hours every Monday morning manually exporting data and building reports for my team. Is there any way to automate this? We need weekly exports sent to our BI tool automatically.',
                'customer_segment': 'enterprise',
                'source_name': 'zendesk',
                'sentiment': 'negative',
                'urgency': 8,
            },
            {
                'evidence_type': 'support_ticket',
                'title': 'CSV export missing columns',
                'text': 'The CSV export is missing the custom fields we added last month. The columns just don\'t appear in the exported file. We rely on these for our sales pipeline analysis.',
                'customer_segment': 'mid_market',
                'source_name': 'zendesk',
                'sentiment': 'negative',
                'urgency': 7,
            },
            {
                'evidence_type': 'interview_transcript',
                'title': 'Enterprise PM Interview - DataCorp',
                'text': 'Interviewer: What\'s your biggest frustration with the product? PM: Honestly, the reporting. I can\'t customize dashboards to show what matters to my team. I end up exporting everything to Google Sheets and building my own charts. The default dashboard shows metrics that aren\'t relevant to my workflow. I need to see pipeline velocity, not just total deals. Also the date ranges are really limited.',
                'customer_segment': 'enterprise',
                'source_name': 'user_research',
                'sentiment': 'negative',
                'urgency': 7,
            },
            {
                'evidence_type': 'interview_transcript',
                'title': 'SMB Founder Interview - StartupXYZ',
                'text': 'When we first signed up, the onboarding was really confusing. There were like 8 steps to configure before we could see anything useful. Two of my team members gave up during setup. I had to walk them through it personally. The product is great once you get past the setup wall, but that first experience almost made us churn.',
                'customer_segment': 'smb',
                'source_name': 'user_research',
                'sentiment': 'mixed',
                'urgency': 6,
            },
            {
                'evidence_type': 'feature_request',
                'title': 'Custom dashboard widgets',
                'text': 'Request: Ability to create custom dashboard widgets that pull specific metrics. Currently limited to pre-built charts. Need: funnel conversion by source, deal velocity by stage, custom date comparisons. Priority for our team as it would replace 3 spreadsheets we maintain manually. 47 upvotes from other customers.',
                'customer_segment': 'enterprise',
                'source_name': 'productboard',
                'sentiment': 'neutral',
                'urgency': 7,
            },
            {
                'evidence_type': 'feature_request',
                'title': 'API rate limit increase',
                'text': 'Our integration hits rate limits every morning during our sync job. We need either higher rate limits for enterprise plans or a bulk API endpoint. Currently failing silently which causes data inconsistencies in our downstream systems. This is the #1 blocker for our integration team.',
                'customer_segment': 'enterprise',
                'source_name': 'productboard',
                'sentiment': 'negative',
                'urgency': 8,
            },
            {
                'evidence_type': 'nps_survey',
                'title': 'NPS Score 6 - Reporting limitations',
                'text': 'Score: 6. Comment: Love the core CRM functionality but the reporting is holding us back. We need better dashboards, custom date ranges, and the ability to schedule reports. Currently spending too much time on manual data work that should be automated.',
                'customer_segment': 'mid_market',
                'source_name': 'nps_survey',
                'sentiment': 'mixed',
                'urgency': 6,
            },
            {
                'evidence_type': 'churn_feedback',
                'title': 'Enterprise churn - MegaCorp',
                'text': 'Reason for leaving: We switched to Competitor X because your export and reporting capabilities couldn\'t scale with our needs. We have 200K contacts and the export would never complete. We needed automated daily syncs to our data warehouse which your product doesn\'t support. ARR impact: $48,000/year.',
                'customer_segment': 'enterprise',
                'source_name': 'exit_survey',
                'sentiment': 'negative',
                'urgency': 10,
            },
            {
                'evidence_type': 'churn_feedback',
                'title': 'SMB churn - QuickStart Inc',
                'text': 'Reason for leaving: Onboarding was too complex. We spent 2 weeks trying to get the team set up and still couldn\'t figure out how to connect our email. The setup wizard is overwhelming for a small team. Went with a simpler tool that got us productive in 10 minutes.',
                'customer_segment': 'smb',
                'source_name': 'exit_survey',
                'sentiment': 'negative',
                'urgency': 7,
            },
            {
                'evidence_type': 'slack_thread',
                'title': 'Community discussion on data export',
                'text': 'Thread with 23 replies. Multiple users discussing workarounds for the export timeout issue. One user shared a script that uses the API to export in chunks. Another suggested a Chrome extension. Consensus: the export feature needs a complete overhaul for large datasets. Enterprise users particularly frustrated.',
                'customer_segment': 'enterprise',
                'source_name': 'slack',
                'sentiment': 'negative',
                'urgency': 8,
            },
            {
                'evidence_type': 'feature_request',
                'title': 'Simplified onboarding wizard',
                'text': 'The current 8-step onboarding wizard has too many required fields. New suggestion: reduce to 3 essential steps (account, team invite, first project) and make advanced config optional. Include a sample project so users can see value immediately. Data shows 40% drop-off at step 4.',
                'customer_segment': 'startup',
                'source_name': 'productboard',
                'sentiment': 'neutral',
                'urgency': 6,
            },
            {
                'evidence_type': 'support_ticket',
                'title': 'Dashboard refresh issues',
                'text': 'The dashboard doesn\'t auto-refresh. I have to manually reload the page every time I want to see updated numbers. In a fast-moving sales environment, this is really disruptive. Competitor dashboards update in real-time.',
                'customer_segment': 'mid_market',
                'source_name': 'zendesk',
                'sentiment': 'negative',
                'urgency': 5,
            },
            {
                'evidence_type': 'analytics_event',
                'title': 'Export feature usage spike and failures',
                'text': 'Analytics data: Export feature used 1,247 times last month. 312 exports failed (25% failure rate). Average export time: 45 seconds for <10K rows, timeout for >10K rows. Top exporters are enterprise segment. 78% of failed exports are from accounts with >50K contacts.',
                'customer_segment': 'enterprise',
                'source_name': 'analytics',
                'sentiment': 'neutral',
                'urgency': 8,
            },
            {
                'evidence_type': 'nps_survey',
                'title': 'NPS Score 9 - Love the product, want better integrations',
                'text': 'Score: 9. Comment: The core CRM is fantastic and the workflow automation saves us hours. Only complaint is the API limitations - we need higher rate limits and better webhook support to connect with our other tools. Would be a 10 if integrations were stronger.',
                'customer_segment': 'enterprise',
                'source_name': 'nps_survey',
                'sentiment': 'positive',
                'urgency': 4,
            },
        ]

        created_evidence = []
        for e_data in evidence_data:
            e, _ = RawEvidence.objects.get_or_create(
                organization=org, project=project,
                title=e_data['title'],
                defaults={
                    **e_data,
                    'created_by': user,
                    'data_source': sources.get(e_data['evidence_type']),
                }
            )
            created_evidence.append(e)

        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(evidence_data)} evidence items created'))

        # Pre-created Insights
        insights_data = [
            {
                'title': 'Data Export Reliability & Performance Crisis',
                'summary': 'Enterprise customers face critical data export failures on large datasets (>10K rows). 25% failure rate observed. Customers report 2-3 hours/week wasted on manual export workarounds. Direct cause of at least one enterprise churn ($48K ARR).',
                'frequency': 34,
                'severity': 'critical',
                'segments_affected': ['enterprise', 'mid_market'],
                'representative_quotes': [
                    'Export times out every time on datasets over 10k rows',
                    'I spend 3 hours every Monday just exporting reports',
                    'We switched to a competitor because exports couldn\'t handle our volume'
                ],
                'trend_direction': 'rising',
                'confidence': 0.92,
                'topics': ['data_export', 'reliability', 'enterprise', 'performance'],
            },
            {
                'title': 'Dashboard Customization & Reporting Gap',
                'summary': 'Users across all segments need customizable dashboards with flexible date ranges, auto-refresh, and role-specific views. Currently forced to use spreadsheets as workaround, defeating the CRM value proposition.',
                'frequency': 28,
                'severity': 'high',
                'segments_affected': ['enterprise', 'mid_market', 'smb'],
                'representative_quotes': [
                    'I can\'t customize dashboards to show what matters to my team',
                    'I end up exporting everything to Google Sheets',
                    'The dashboard doesn\'t auto-refresh'
                ],
                'trend_direction': 'rising',
                'confidence': 0.87,
                'topics': ['dashboard', 'customization', 'reporting', 'analytics'],
            },
            {
                'title': 'Onboarding Friction Causing SMB Churn',
                'summary': 'New users, especially in SMB/startup segments, struggle with the 8-step onboarding wizard. 40% drop-off rate at step 4. Teams abandon setup or require manual hand-holding. Multiple churn cases cite complex onboarding.',
                'frequency': 22,
                'severity': 'high',
                'segments_affected': ['smb', 'startup'],
                'representative_quotes': [
                    'Two of my team members gave up during setup',
                    'The setup wizard is overwhelming for a small team',
                    '40% drop-off at step 4'
                ],
                'trend_direction': 'stable',
                'confidence': 0.84,
                'topics': ['onboarding', 'activation', 'ux', 'churn'],
            },
            {
                'title': 'API Rate Limiting Blocking Enterprise Integrations',
                'summary': 'Enterprise customers hit API rate limits during peak sync hours, causing data inconsistencies. Requests for higher limits or bulk endpoints. Integration reliability is key enterprise requirement.',
                'frequency': 15,
                'severity': 'medium',
                'segments_affected': ['enterprise'],
                'representative_quotes': [
                    'Our sync job fails every morning because of rate limits',
                    'Rate limit errors don\'t provide enough info to debug',
                    'Need higher limits or a bulk endpoint'
                ],
                'trend_direction': 'rising',
                'confidence': 0.79,
                'topics': ['api', 'developer_experience', 'integration', 'enterprise'],
            },
        ]

        created_insights = []
        for i_data in insights_data:
            insight, _ = InsightCluster.objects.get_or_create(
                organization=org, project=project,
                title=i_data['title'],
                defaults={
                    **i_data,
                    'created_by': user,
                }
            )
            # Link evidence
            insight.evidence_refs.set(created_evidence[:5])
            created_insights.append(insight)

        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(insights_data)} insight clusters created'))

        # Opportunities
        opps_data = [
            {
                'title': 'Automated Data Export Pipeline',
                'problem_statement': 'Enterprise customers waste 2-3 hours weekly on manual data exports that fail on large datasets (25% failure rate). Direct churn risk with $48K+ ARR impact per account.',
                'affected_segments': ['enterprise', 'mid_market'],
                'proposed_solution': 'Build scheduled export system with background processing, progress tracking, multiple formats (CSV, JSON, Parquet), and webhook notifications.',
                'assumptions': ['Users will adopt scheduled exports over manual', 'Background processing handles up to 1M rows', 'Enterprise customers see measurable time savings'],
                'risks': ['Infrastructure cost for large exports', 'Format compatibility across BI tools', 'Storage infrastructure changes needed'],
                'alternatives': ['Direct BI tool integrations', 'Real-time streaming API', 'Partner with Fivetran/Airbyte'],
                'implementation_outline': 'Phase 1: Background job processor + progress API (2w). Phase 2: Scheduling + formats (2w). Phase 3: Webhooks + connectors (2w).',
                'status': 'evaluating',
            },
            {
                'title': 'Customizable Dashboard Builder',
                'problem_statement': 'Users cannot tailor dashboards to role-specific needs, forcing workarounds with spreadsheets. Affects daily value perception and engagement.',
                'affected_segments': ['enterprise', 'mid_market', 'smb'],
                'proposed_solution': 'Drag-and-drop dashboard builder with configurable widgets, custom date ranges, auto-refresh, and shareable layouts.',
                'assumptions': ['Users will invest time in configuration', 'Custom dashboards increase DAU', 'Widget library covers 80% of needs'],
                'risks': ['Complex frontend engineering', 'Performance with many widgets', 'Permission complexity'],
                'alternatives': ['Pre-built role templates', 'Embed Metabase/Grafana', 'Custom report builder'],
                'implementation_outline': 'Phase 1: Widget framework + drag-drop (4w). Phase 2: Date ranges + refresh (2w). Phase 3: Sharing + templates (2w).',
                'status': 'discovered',
            },
            {
                'title': 'Streamlined 3-Step Onboarding',
                'problem_statement': 'SMB/startup users face 40% drop-off in current 8-step onboarding. Multiple churns cite setup complexity as primary reason.',
                'affected_segments': ['smb', 'startup'],
                'proposed_solution': 'Reduce to 3 steps: account creation, team invite, sample project. Advanced configuration deferred to post-activation. Include interactive product tour.',
                'assumptions': ['Fewer steps = higher completion', 'Sample project drives aha moment', 'Deferred config acceptable'],
                'risks': ['Missing critical setup for some users', 'Increased support for config later', 'May need team discovery features'],
                'alternatives': ['Video onboarding guide', 'Concierge onboarding for paid plans', 'Progressive disclosure approach'],
                'implementation_outline': 'Phase 1: Simplified wizard (2w). Phase 2: Sample project template (1w). Phase 3: Interactive tour (2w).',
                'status': 'discovered',
            },
        ]

        created_opps = []
        for i, o_data in enumerate(opps_data):
            opp, _ = Opportunity.objects.get_or_create(
                organization=org, project=project,
                title=o_data['title'],
                defaults={
                    **o_data,
                    'created_by': user,
                }
            )
            if created_insights:
                opp.supporting_insights.set(created_insights[:2] if i == 0 else [created_insights[min(i, len(created_insights)-1)]])
            opp.evidence_refs.set(created_evidence[:4])
            created_opps.append(opp)

        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(opps_data)} opportunities created'))

        # Score the first opportunity
        if created_opps:
            score, _ = OpportunityScore.objects.get_or_create(
                opportunity=created_opps[0],
                organization=org,
                project=project,
                defaults={
                    'frequency_score': 8.5,
                    'revenue_impact': 7.8,
                    'retention_impact': 8.2,
                    'strategic_alignment': 7.0,
                    'effort_estimate': 5.5,
                    'confidence_score': 0.85,
                    'created_by': user,
                }
            )
            score.calculate_score()
            self.stdout.write(self.style.SUCCESS(f'  ✓ Opportunity scored: {score.total_score:.2f}'))

            # Score second opp
            if len(created_opps) > 1:
                score2, _ = OpportunityScore.objects.get_or_create(
                    opportunity=created_opps[1],
                    organization=org,
                    project=project,
                    defaults={
                        'frequency_score': 7.2,
                        'revenue_impact': 6.5,
                        'retention_impact': 7.0,
                        'strategic_alignment': 7.5,
                        'effort_estimate': 7.0,
                        'confidence_score': 0.78,
                        'created_by': user,
                    }
                )
                score2.calculate_score()

            if len(created_opps) > 2:
                score3, _ = OpportunityScore.objects.get_or_create(
                    opportunity=created_opps[2],
                    organization=org,
                    project=project,
                    defaults={
                        'frequency_score': 6.8,
                        'revenue_impact': 5.5,
                        'retention_impact': 6.0,
                        'strategic_alignment': 6.5,
                        'effort_estimate': 4.0,
                        'confidence_score': 0.82,
                        'created_by': user,
                    }
                )
                score3.calculate_score()

        # Create a sample spec
        if created_opps:
            artifact, _ = GeneratedArtifact.objects.get_or_create(
                organization=org, project=project,
                opportunity=created_opps[0],
                title=f'PRD: {created_opps[0].title}',
                defaults={
                    'artifact_type': 'prd',
                    'current_version': 1,
                    'status': 'draft',
                    'created_by': user,
                }
            )

            ArtifactVersion.objects.get_or_create(
                artifact=artifact, version_number=1,
                organization=org, project=project,
                defaults={
                    'content': {
                        'prd': {
                            'title': 'Automated Data Export Pipeline',
                            'version': '1.0',
                            'overview': 'Build a scheduled, reliable data export system for enterprise customers.',
                            'goals': ['Reduce manual export time to 0', 'Support 1M+ rows', 'Enable scheduling'],
                            'non_goals': ['Real-time streaming', 'Custom ETL'],
                        },
                        'user_stories': [
                            {'role': 'Enterprise Admin', 'action': 'schedule weekly export', 'benefit': 'automated BI updates'},
                        ],
                        'readiness_score': {'total': 45, 'validation_rules': True, 'error_states': False, 'edge_cases': False, 'performance_requirements': True, 'security_requirements': False},
                    },
                    'change_summary': 'Initial draft generated by AI',
                    'readiness_score': 45,
                    'created_by': user,
                }
            )
            self.stdout.write(self.style.SUCCESS('  ✓ Sample spec created'))

        # Notifications
        Notification.objects.get_or_create(
            user=user, notification_type='opportunity_discovered',
            title='New Opportunity: Automated Data Export Pipeline',
            defaults={
                'message': 'AI discovered a high-priority opportunity based on 34 evidence items.',
                'organization': org,
            }
        )
        Notification.objects.get_or_create(
            user=user, notification_type='spec_ready',
            title='Spec ready for review: PRD Data Export Pipeline',
            defaults={
                'message': 'The AI-generated PRD is ready for your review. Readiness score: 45%.',
                'organization': org,
            }
        )

        self.stdout.write(self.style.SUCCESS('\n🎉 PMBrain AI demo data seeded successfully!'))
        self.stdout.write(self.style.SUCCESS('   Login: demo@pmbrain.ai / demo1234'))
        self.stdout.write(self.style.SUCCESS('   Organization: Acme SaaS'))
        self.stdout.write(self.style.SUCCESS('   Project: Acme CRM'))
