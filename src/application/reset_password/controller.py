import random
import typing as t
from http import HTTPStatus

from arcs_lib_pca.application import BaseController
from arcs_lib_pca.tools.notify import Notification, TargetNotification, EmailDynamicData
from arcs_lib_pca.domain import DateTime

from src.infrastructure.models import UserModel

from .requests import (
    SendResetPasswordRequest,
    ValidateCodeRequest,
    ResetPasswordRequest,
    ForceResetPasswordRequestAuth, ResetPasswordAuthenticatedAuthRequest,
)
from .responses import(
    SendCodeResponse,
    ValidateCodeResponse,
    ResetPasswordResponse,
)

class ResetPasswordController(BaseController):
    __CACHE_EXPIRATION_TIME : int = 600
    
    @BaseController.route(
        path="/",
        methods=["POST"],
        request=SendResetPasswordRequest,
        response=SendCodeResponse)
    def send_reset_code(self, req: SendResetPasswordRequest, resp: SendCodeResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")
        
        user_repo = self.load_repository(UserModel)
        user : UserModel = user_repo.db.get_by(email=req.email, load=["person"])

        if not user:
            return resp(HTTPStatus.OK, message="Reset code sent")

        user_dict = user.to_dict(lazy_load=["person"])
        redis_key = f"@code:type:reset_password:user:{user.id}"

        old_code = self.get_redis().get_by_key(redis_key)

        minutes_to_wait = 2
        if old_code and (old_expiration := old_code.get("expiration")):
            if DateTime.from_string(old_expiration).difference_in_minutes(DateTime.now(), absolute=True) < minutes_to_wait: 
                return resp(HTTPStatus.BAD_REQUEST, message=f"Code already sent in the last {minutes_to_wait} minutes")

        # Gerar código de 4 dígitos
        code = str(random.randint(0, 9999)).zfill(4)
        
        expiration = DateTime.now().add_minutes(ResetPasswordController.__CACHE_EXPIRATION_TIME//10)

        # Salvar no Redis
        redis_data = {
            "email": req.email,
            "code": code,
            "expiration": expiration,
            "validated": False
        }        
        
        if not old_code:
            self.get_redis().add(redis_key, redis_data, ex=ResetPasswordController.__CACHE_EXPIRATION_TIME)
        else:
            self.get_redis().update(redis_key, redis_data, ex=ResetPasswordController.__CACHE_EXPIRATION_TIME)
        user_name = user_dict.get("person", {}).get("full_name")

        # Send email with reset code
        self._send_reset_code_email(
            target_name=user_name,
            target_email=req.email,
            code=code
        )
        
        return resp(HTTPStatus.OK, message="Reset code sent")

    @BaseController.route(
        path="/code/",
        methods=["POST"],
        request=ValidateCodeRequest,
        response=ValidateCodeResponse
    )
    def validate_code(self, req: ValidateCodeRequest, resp: ValidateCodeResponse):
        user_repo = self.load_repository(UserModel)
        user : UserModel = user_repo.db.get_by(email=req.email)

        if not user:
            return resp(HTTPStatus.NOT_FOUND, message="User not found")

        redis_key = f"@code:type:reset_password:user:{user.id}"
        stored_data = self.get_redis().get_by_key(redis_key)

        if not stored_data or stored_data["code"] != req.code:
            return resp(HTTPStatus.BAD_REQUEST, message="Invalid or expired code")

        stored_data["validated"] = True
        self.get_redis().add(redis_key, stored_data, ex=ResetPasswordController.__CACHE_EXPIRATION_TIME)

        return resp(HTTPStatus.OK, message="Code validated successfully")

    @BaseController.route(
        path="/authenticated/",
        methods=["PUT"],
        request=ResetPasswordAuthenticatedAuthRequest,
        response=ResetPasswordResponse
    )
    def reset_password_authenticated(self, req: ResetPasswordAuthenticatedAuthRequest, resp: ResetPasswordResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        user_repo = self.load_repository(UserModel)
        user : UserModel = user_repo.db.get_by_id(req.current_profile.user_id)

        if not user:
            return resp(HTTPStatus.NOT_FOUND, message="User not found")

        if not user.verify_password(req.old_password):
            return resp(HTTPStatus.UNAUTHORIZED, message="Old password does not match")

        user.set_password(req.new_password)
        user_repo.db.update_by_id(user.id, {"password": user.password, "salt": user.salt})

        return resp(HTTPStatus.OK, message="Password reset successfully")

    @BaseController.route(
        path="/",
        methods=["PUT"],
        request=ResetPasswordRequest,
        response=ResetPasswordResponse)
    def reset_password(self, req: ResetPasswordRequest, resp: ResetPasswordResponse):
        user_repo = self.load_repository(UserModel)
        user : UserModel = user_repo.db.get_by(email=req.email)

        if not user:
            return resp(HTTPStatus.NOT_FOUND, message="User not found")

        redis_key = f"@code:type:reset_password:user:{user.id}"
        stored_data = self.get_redis().get_by_key(redis_key) 

        if not stored_data or not stored_data["validated"] or stored_data["code"] != req.code:
            return resp(HTTPStatus.BAD_REQUEST, message="Invalid or expired code")

        user.set_password(req.new_password)
        user_repo.db.update_by_id(user.id, {"password": user.password, "salt": user.salt})
        
        # Delete no Redis precisa da chave em array e os dados
        self.get_redis().remove(redis_key)

        return resp(HTTPStatus.OK, message="Password reset successfully")

    
    @BaseController.route(
        path="/force/",
        methods=["PUT"],
        request=ForceResetPasswordRequestAuth,
        response=ResetPasswordResponse)
    def force_reset_password(self, req: ForceResetPasswordRequestAuth, resp: ResetPasswordResponse):
        user_repo = self.load_repository(UserModel)
        user : UserModel = user_repo.db.get_by(email=req.email)

        if not req.current_profile.group_name.upper() in ["ADMIN", "OWNER"]:
            return resp(HTTPStatus.FORBIDDEN, message="Access denied")

        if not user:
            return resp(HTTPStatus.NOT_FOUND, message="User not found")

        user.set_password(req.new_password)
        user_repo.db.update_by_id(user.id, {"password": user.password, "salt": user.salt})

        return resp(HTTPStatus.OK, message="Password reset successfully")

    def _send_reset_code_email(self, target_email: str, code: str, target_name: t.Optional[str] =None):
        self.notify.send_email(
            notification=Notification(
                channel_names=["EMAIL"],
                targets=[TargetNotification(
                    target_type=["USER"],
                    target_name=target_name or "espero que esteja bem!",
                    target_address=target_email
                )],
                subject="Código de Redefinição de Senha - Porsche Cup Brasil",
                template_id=self._app.settings.sendgrid_template_default_id,
                meta_data=EmailDynamicData(
                    body_text=f"""
                        <p style="font-size: 16px; line-height: 1.5;">Olá, {target_name}</p>
                        <p style="font-size: 16px; line-height: 1.5;">Recebemos uma solicitação para redefinir sua senha na aplicação da Porche Cup Pilot.</p>
                        <p style="font-size: 16px; line-height: 1.5;">Seu código de verificação é:</p>
                        <div style="text-align: center; margin: 20px 0;">
                            <span style="font-size: 32px; font-weight: bold; padding: 10px 20px; background-color: #000000; color: #ffffff; border-radius: 4px;">{code}</span>
                        </div>
                        <p style="font-size: 16px; line-height: 1.5;">Insira este código na tela de verificação dentro de 10 minutos para redefinir sua senha.</p>
                        <p style="font-size: 16px; line-height: 1.5;">Se você não solicitou, ignore este e-mail e fale conosco.</p>
                        <p style="font-size: 12px; line-height: 1.5;"><em>Este e-mail foi enviado automaticamente, por favor não responda.</em></p>
                    """,
                    cta_label="",
                    cta_url=""
                ).model_dump()
            )
        )

