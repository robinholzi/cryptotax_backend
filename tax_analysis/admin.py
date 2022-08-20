from django.contrib import admin

from tax_analysis.models import (
    Analysable,
    AnalysisBuy,
    AnalysisConsumable,
    AnalysisConsumer,
    AnalysisDeposit,
    AnalysisSell,
    AnalysisSellConsumer,
    AnalysisTransfer,
    AnalysisTransferConsumer,
    PortfolioAnalysis,
    PortfolioAnalysisReport,
    ProcessableDeposit,
    ProcessableOrder,
    ProcessableTransaction,
    ProcessableTransfer,
)

admin.site.register(PortfolioAnalysis)
admin.site.register(PortfolioAnalysisReport)

admin.site.register(ProcessableTransaction)
admin.site.register(ProcessableOrder)
admin.site.register(ProcessableDeposit)
admin.site.register(ProcessableTransfer)

admin.site.register(Analysable)
admin.site.register(AnalysisBuy)
admin.site.register(AnalysisConsumable)
admin.site.register(AnalysisSell)
admin.site.register(AnalysisDeposit)
admin.site.register(AnalysisTransfer)
admin.site.register(AnalysisConsumer)
admin.site.register(AnalysisSellConsumer)
admin.site.register(AnalysisTransferConsumer)
