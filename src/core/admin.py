from django import forms
from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.shortcuts import render

from .models import UserProfile

User = get_user_model()


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'is_participant', 'profile_picture_url')
    list_filter = ('is_participant',)
    search_fields = ('user__username', 'user__email')


class GroupActionForm(forms.Form):
    """Form de la página intermedia del action de grupos."""
    group = forms.ModelChoiceField(queryset=Group.objects.all(), label='Grupo')
    operation = forms.ChoiceField(
        choices=[('add', 'Agregar al grupo'), ('remove', 'Quitar del grupo')],
        widget=forms.RadioSelect, initial='add', label='Operación',
    )


# Reemplaza el admin por defecto de User: muestra "Activo" y "Participa",
# y agrega actions (toggle activo, asignar/quitar grupo).
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'participa')
    list_filter = UserAdmin.list_filter + ('profile__is_participant', 'groups')
    actions = ['toggle_active', 'manage_group']

    @admin.display(boolean=True, description='Participa')
    def participa(self, obj):
        return getattr(getattr(obj, 'profile', None), 'is_participant', False)

    @admin.action(description='Activar / desactivar los usuarios seleccionados')
    def toggle_active(self, request, queryset):
        # Invierte is_active por cada usuario: activos → inactivos y viceversa.
        # Capturo los ids ANTES de actualizar para que el segundo update no
        # vuelva a tomar los recién activados.
        to_activate = list(queryset.filter(is_active=False).values_list('id', flat=True))
        to_deactivate = list(queryset.filter(is_active=True).values_list('id', flat=True))
        activated = User.objects.filter(id__in=to_activate).update(is_active=True)
        deactivated = User.objects.filter(id__in=to_deactivate).update(is_active=False)
        self.message_user(
            request,
            f'{activated} activado(s) y {deactivated} desactivado(s).',
        )

    @admin.action(description='Asignar / quitar grupo…')
    def manage_group(self, request, queryset):
        # Página intermedia: elegir grupo + operación (agregar/quitar) y aplicar.
        if 'apply' in request.POST:
            form = GroupActionForm(request.POST)
            if form.is_valid():
                group = form.cleaned_data['group']
                op = form.cleaned_data['operation']
                for user in queryset:
                    if op == 'add':
                        user.groups.add(group)
                    else:
                        user.groups.remove(group)
                verb = 'agregado(s) a' if op == 'add' else 'quitado(s) de'
                self.message_user(
                    request, f'{queryset.count()} usuario(s) {verb} el grupo "{group.name}".'
                )
                return None  # vuelve al changelist
        else:
            form = GroupActionForm()
        return render(request, 'admin/core/assign_group.html', {
            'title': 'Asignar / quitar grupo',
            'users': queryset,
            'form': form,
            'selected': request.POST.getlist(ACTION_CHECKBOX_NAME),
            'opts': self.model._meta,
        })
