from django.contrib import admin
import breeze.models
import shiny.models
# import breeze.models as breeze_models

admin.site.register(breeze.models.Rscripts)
admin.site.register(breeze.models.Jobs)
admin.site.register(breeze.models.UserProfile)
admin.site.register(breeze.models.DataSet)
admin.site.register(breeze.models.InputTemplate)
admin.site.register(breeze.models.Report)
admin.site.register(breeze.models.ReportType)
admin.site.register(breeze.models.Project)
admin.site.register(breeze.models.Post)
admin.site.register(breeze.models.Group)
# admin.site.register(breeze_models.Statistics)
# admin.site.register(breeze_models.ShinyApp)
admin.site.register(breeze.models.OffsiteUser)
# admin.site.register(breeze_models.ShinyReport, prepopulated_fields = { 'custom_header': ['title'], })
admin.site.register(shiny.models.ShinyReport )
admin.site.register(shiny.models.ShinyTag)
admin.site.register(breeze.models.ComputeTarget) # 19/04/2016
admin.site.register(breeze.models.EngineConfig) # 13/05/2016
admin.site.register(breeze.models.ExecConfig) # 13/05/2016
admin.site.register(breeze.models.Institute) # 23/06/2016


