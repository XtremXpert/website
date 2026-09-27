# Copyright 2020 Advitus MB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
from pathlib import Path

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _dispatch(cls, endpoint):
        res = cls._check_require_auth()
        if res:
            return res
        return super()._dispatch(endpoint)

    @classmethod
    def _serve_fallback(cls):
        res = cls._check_require_auth()
        if res:
            return res
        return super()._serve_fallback()

    @classmethod
    def _check_require_auth(cls):
        # if not website request - skip
        # Odoo 20: the current website comes from the context (env.website); before the
        # website's own fallback runs, only the host's website (host_id) may be known.
        website = request.env.website
        if not website and request.env.context.get("host_id"):
            website = request.env["website"].browse(request.env.context["host_id"])
        if not website:
            return None
        website = website.sudo()
        if request.env.uid and (request.env.uid != website.user_id.id):
            return None
        auth_paths = (
            request.env["website.auth.url"]
            .sudo()
            .search(
                [
                    ("website_id", "=", website.id),
                ]
            )
            .mapped("path")
        )
        path = request.httprequest.path
        for auth_path in auth_paths:
            if auth_path == path or Path(auth_path) in Path(path).parents:
                redirect_path = f"/web/login?redirect={path}"
                return request.redirect(redirect_path, code=302)
