# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import List

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor, _get_route_details
from opentelemetry.instrumentation.fastapi.version import __version__  # noqa

from atlas_tracing.integrations.asgi import ASGIMiddleware


class AtlasFastAPIInstrumentor(FastAPIInstrumentor):
    """An instrumentor for FastAPI

    See `BaseInstrumentor`
    """

    _original_fastapi = None

    @staticmethod
    def instrument_app(app, span_callback=None, ignored_paths: List[str] = None):
        """Instrument an uninstrumented FastAPI application.
        """
        callback = _get_route_details if not span_callback else span_callback
        if not getattr(app, "is_instrumented_by_opentelemetry", False):
            app.add_middleware(
                ASGIMiddleware,
                span_details_callback=callback,
                ignored_paths=ignored_paths
            )
            app.is_instrumented_by_opentelemetry = True
