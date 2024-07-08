FROM python:3-alpine AS build
COPY ./ /app
RUN cd /app && pip install build && python -m build -w
RUN cd /app/dist && pip wheel --cache-dir ../_cache --find-links ../_cache -r ../requirements.txt

FROM python:3-alpine
ENV PYTHONDONTWRITEBYTECODE=1
COPY --from=build /app/dist/*.whl /dist/
RUN --mount=type=cache,target=/root/.cache pip install --no-compile /dist/*.whl
ENTRYPOINT ["pstyle"]
