"""
Created by nicolas.looschen@pikobytes.de on 10.07.2024.

This file is subject to the terms and conditions defined in
file 'LICENSE.txt', which is part of this source code package.
"""

from typing import Annotated, Union

import requests
from loguru import logger
from fastapi import Cookie, HTTPException, Depends, Header

from georeference.config.settings import get_settings, Settings
from georeference.schemas.user import User, UserResponse

http_session = requests.Session()


def get_user_from_session(
    settings: Annotated[Settings, Depends(get_settings)],
    fe_typo_user: Annotated[Union[None, str], Cookie()] = None,
    dev_mode_secret: Annotated[str | None, Header()] = None,
    dev_mode_name: Annotated[str | None, Header()] = None,
):
    try:
        # Bypass authentication in development mode with secret
        if settings.DEV_MODE and settings.DEV_MODE_SECRET:
            # A valid DEV_MODE_SECRET must always have more then 10 characters. This condition should
            # prevent miss configuration of the DEV_MODE_SECRET
            if (
                dev_mode_secret == settings.DEV_MODE_SECRET
                and len(settings.DEV_MODE_SECRET) > 10
            ):
                return User(
                    username=dev_mode_name,
                    uid=-1,
                    groups=[settings.USER_ROLE, settings.ADMIN_ROLE],
                )

        response = http_session.get(
            f"{settings.TYPO3_URL}/?tx_slubwebkartenforum_georeference[controller]=Georef&tx_slubwebkartenforum_georeference[action]=getSession&type=9991",
            cookies={"fe_typo_user": fe_typo_user},
            # In development mode we don't verify the SSL certificate, because the ddev site uses a self-signed certificate
            # and setting it up to be trusted is a hassle.
            verify=False if settings.DEV_MODE else True,
        )
        if response.status_code == 200:
            user_response = UserResponse.model_validate_json(response.text)
            if user_response.valid:
                return user_response.userData

        return None
    except Exception as e:
        logger.error("Error while fetching user from session: {}", e)
        return None


def require_authenticated_user(user: Annotated[User, Depends(get_user_from_session)]):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_user_role(role: str):
    def _require_user_role(user: User = Depends(require_authenticated_user)):
        if role not in user.groups:
            raise HTTPException(status_code=403, detail="Not authorized")
        return user

    return _require_user_role
