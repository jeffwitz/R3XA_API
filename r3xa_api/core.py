# -*- coding: utf-8 -*-
"""
Created on Tue Sep  1 11:06:57 2026

@author: passieux
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonschema

from .registry import load_item, save_item
from .schema import load_schema

from .schemaplot import Case, generate_block_diagram

from .new_setting import *
from .new_datasource import *
from .new_dataset import *

def unit(
    title: Optional[str] = None,
    value: Optional[float] = None,
    unit: Optional[str] = None,
    scale: Optional[float] = 1.0,
    **extra: Any,
) -> Dict[str, Any]:
    """Build a unit payload compatible with R3XA schema."""

    payload = {
        "kind": "unit",
    }
    if unit is None:
        raise TypeError("unit requires the `unit` field")
    payload["unit"] = unit
    if title is not None:
        payload["title"] = title
    if value is not None:
        payload["value"] = value
    if scale is not None:
        payload["scale"] = scale
    payload.update(extra)
    return payload

def data_set_file(filename: str, delimiter: Optional[str] = None, data_range: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
    """Build a `data_set_file` payload for `timestamps` or `data` fields."""

    payload = {
        "kind": "data_set_file",
        "filename": filename,
    }
    if delimiter is not None:
        payload["delimiter"] = delimiter
    if data_range is not None:
        if not isinstance(data_range, str):
            raise TypeError("data_range must be a string or None")
        payload["data_range"] = data_range
    payload.update(extra)
    return payload

class R3XAFile:
    """
    R3XA experiment description.

    Attributes
    ----------
    title : str
        Title of the data sets. Required.
    description : str
        Description of the data sets. Required.
    version : str
        Version of the schema used. Required.
    authors : str
        Names, ORCID, IDHAL... Required.
    date : str
        Global date of the experiment (YYYY-MM-DD). Required.
    repository : str, optional
        URL to the repository where the dataset is stored.
    documentation : str, optional
        URI to the documentation (pdf).
    license : str, optional
        Public domain, CC-BY, ...
    settings : list[Setting]
        Experimental parameters and setups.
    data_sources : list[DataSource]
        Procedures or systems that generate data sets.
    data_sets : list[Dataset]
        Measured or generated data.
    """

    _required_fields = {
        "title",
        "description",
        "version",
        "authors",
        "date",
    }

    def __init__(
        self,
        title: str,
        description: str,
        authors: str,
        date: str,
        version: str | None = None,
        repository: str | None = None,
        documentation: str | None = None,
        license: str | None = None,
        settings: list[Setting] | None = None,
        data_sources: list[DataSource] | None = None,
        data_sets: list[Dataset] | None = None,
    ) -> None:
        """
        Create an R3XA file.

        Parameters
        ----------
        title : str
            Title of the data sets.
        description : str
            Description of the data sets.
        authors : str
            Names, ORCID, IDHAL...
        date : str
            Global date of the experiment (YYYY-MM-DD).
        version : str, optional
            Version of the schema used. If omitted, the current
            schema version is used automatically.
        repository : str, optional
            URL to the repository where the dataset is stored.
        documentation : str, optional
            URI to the documentation.
        license : str, optional
            License information.
        settings : list[Setting], optional
            List of experimental settings.
        data_sources : list[DataSource], optional
            List of data sources.
        data_sets : list[Dataset], optional
            List of datasets.
        """

        self.title = title
        self.description = description
        self.authors = authors
        self.date = date

        # The schema defines version as a constant.
        # We therefore use the schema value automatically.
        if version is None:
            schema = load_schema()
            version = schema["properties"]["version"]["const"]

        self.version = version

        # Optional header fields are deliberately kept as None.
        self.repository = repository
        self.documentation = documentation
        self.license = license

        # Lists are initialized as empty lists rather than None.
        self.settings = (
            [] if settings is None else list(settings)
        )

        self.data_sources = (
            [] if data_sources is None else list(data_sources)
        )

        self.data_sets = (
            [] if data_sets is None else list(data_sets)
        )

    # ==================================================================
    # Conversion
    # ==================================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the complete R3XA object to a Python dictionary.

        Optional header fields whose value is None are omitted from
        the resulting dictionary.

        Settings, data sources and datasets are converted using their
        own to_dict() methods.
        """

        data: dict[str, Any] = {}

        # --------------------------------------------------------------
        # Header
        # --------------------------------------------------------------

        data["title"] = self.title
        data["description"] = self.description
        data["version"] = self.version
        data["authors"] = self.authors
        data["date"] = self.date

        if self.repository is not None:
            data["repository"] = self.repository

        if self.documentation is not None:
            data["documentation"] = self.documentation

        if self.license is not None:
            data["license"] = self.license

        # --------------------------------------------------------------
        # Settings
        # --------------------------------------------------------------

        if self.settings:
            data["settings"] = [
                setting.to_dict()
                for setting in self.settings
            ]

        # --------------------------------------------------------------
        # Data sources
        # --------------------------------------------------------------

        if self.data_sources:
            data["data_sources"] = [
                source.to_dict()
                for source in self.data_sources
            ]

        # --------------------------------------------------------------
        # Data sets
        # --------------------------------------------------------------

        if self.data_sets:
            data["data_sets"] = [
                dataset.to_dict()
                for dataset in self.data_sets
            ]

        return data

    # ==================================================================
    # Validation
    # ==================================================================

    def validate(self) -> None:
        """
        Validate the complete R3XA object against schema.json.

        Unlike registry.validate_item(), which validates an individual
        registry object using its kind, this method validates the
        complete R3XA document against the root schema.
        """

        schema = load_schema()

        validator = jsonschema.Draft202012Validator(schema)

        errors = sorted(
            validator.iter_errors(self.to_dict()),
            key=jsonschema.exceptions.relevance,
        )

        if errors:
            message = "\n".join(
                f"- {error.message}"
                for error in errors
            )

            raise jsonschema.exceptions.ValidationError(
                message
            )

    # ==================================================================
    # Save
    # ==================================================================

    def save(
        self,
        path: str | Path,
        *,
        validate: bool = True,
    ) -> Path:
        """
        Save the complete R3XA document to a JSON file.

        Parameters
        ----------
        path : str or pathlib.Path
            Destination JSON file.
        validate : bool, optional
            Validate the document before saving.
        """

        payload = self.to_dict()

        if validate:
            self.validate()

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # We intentionally don't use registry.save_item() here because
        # registry.save_item() is designed for registry entries and
        # validates using a `kind`. The R3XA root document has no kind.
        import json

        path.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        return path

    # ==================================================================
    # Load
    # ==================================================================

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        validate: bool = True,
    ) -> R3XA:
        """
        Load a complete R3XA document from a JSON file.

        Parameters
        ----------
        path : str or pathlib.Path
            JSON file to load.
        validate : bool, optional
            Validate the document after loading.
        """

        import json

        path = Path(path)

        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if validate:
            schema = load_schema()

            validator = jsonschema.Draft202012Validator(
                schema
            )

            errors = sorted(
                validator.iter_errors(payload),
                key=jsonschema.exceptions.relevance,
            )

            if errors:
                message = "\n".join(
                    f"- {error.message}"
                    for error in errors
                )

                raise jsonschema.exceptions.ValidationError(
                    message
                )

        return cls.from_dict(payload)

    # ==================================================================
    # From dictionary
    # ==================================================================

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> R3XA:
        """
        Create an R3XA object from a dictionary.

        The `kind` field of each child object is used by the generated
        classes to reconstruct the appropriate specialized class.
        """

        data = dict(payload)

        settings_payloads = data.pop(
            "settings",
            [],
        )

        data_sources_payloads = data.pop(
            "data_sources",
            [],
        )

        data_sets_payloads = data.pop(
            "data_sets",
            [],
        )

        settings = [
            Setting.from_dict(item)
            for item in settings_payloads
        ]

        data_sources = [
            DataSource.from_dict(item)
            for item in data_sources_payloads
        ]

        data_sets = [
            Dataset.from_dict(item)
            for item in data_sets_payloads
        ]

        return cls(
            **data,
            settings=settings,
            data_sources=data_sources,
            data_sets=data_sets,
        )

    # ==================================================================
    # Pretty plotting
    # ==================================================================

    # def plot(self, **kwargs):
    #     cases = []
    #     # for data in self.settings:
    #     #     cases += [Case(data.id, data.title, [], "#c4894f")]
    #     for data in self.settings:
    #         if data.associated_data_sources is None:
    #             cases += [Case(data.id, data.title, [], "#c4894f")]
    #         else:
    #             cases += [Case(data.id, data.title, data.associated_data_sources, "#c4894f")]
    #     for data in self.data_sources:
    #         if data.input_data_sets is not None:
    #             cases += [Case(data.id, data.title,
    #                       data.input_data_sets, "#bf0040")]
    #         else:
    #             cases += [Case(data.id, data.title, [], "#bf0040")]
    #     for data in self.data_sets:
    #         cases += [Case(data.id, data.title, data.data_sources,
    #                   "#038181"), ]
    #     generate_block_diagram(cases, **kwargs)
    def plot(self, **kwargs):
        cases = []

        # Settings
        # Les associated_data_sources sont des enfants,
        # donc le setting n'a pas de parent à renseigner ici.
        for data in self.settings:
            cases.append(
                Case(data.id, data.title, [], "#c4894f")
            )

        # Data sources
        # Les parents sont les settings associés + les input_data_sets
        for data in self.data_sources:
            parents = []

            # Ajouter les settings qui ont cette data_source comme enfant
            for setting in self.settings:
                if hasattr(setting, 'associated_data_sources'):
                    if setting.associated_data_sources:
                        if data.id in setting.associated_data_sources:
                            parents.append(setting.id)

            # Ajouter les data_sets parents
            if data.input_data_sets:
                parents.extend(data.input_data_sets)

            cases.append(
                Case(data.id, data.title, parents, "#bf0040")
            )

        # Data sets
        for data in self.data_sets:
            cases.append(
                Case(data.id, data.title, data.data_sources, "#038181")
            )
        print(cases)
        generate_block_diagram(cases, **kwargs)

    # ==================================================================
    # Pretty printing
    # ==================================================================

    @staticmethod
    def _format_list_titles(
        objects: list[Any],
    ) -> str:
        """
        Return a compact representation containing only object titles.
        """

        titles = []

        for obj in objects:
            title = getattr(
                obj,
                "title",
                None,
            )

            if title is None:
                titles.append("None")
            else:
                titles.append(str(title))

        return "[" + ", ".join(titles) + "]"

    def _format_attributes(self) -> str:
        """Format the R3XA header and child object lists."""

        attributes = {
            "title": self.title,
            "description": self.description,
            "version": self.version,
            "authors": self.authors,
            "date": self.date,
            "repository": self.repository,
            "documentation": self.documentation,
            "license": self.license,
        }

        display_names = {
            "title": "title*",
            "description": "description",
            "version": "version*",
            "authors": "authors*",
            "date": "date*",
            "repository": "repository",
            "documentation": "documentation",
            "license": "license",
        }

        display_names["settings"] = "settings"
        display_names["data_sources"] = "datasources"
        display_names["data_sets"] = "datasets"

        attributes["settings"] = (
            self._format_list_titles(
                self.settings
            )
        )

        attributes["data_sources"] = (
            self._format_list_titles(
                self.data_sources
            )
        )

        attributes["data_sets"] = (
            self._format_list_titles(
                self.data_sets
            )
        )

        key_width = max(
            len(name)
            for name in display_names.values()
        )

        lines = [
            "R3XA File",
            "─" * max(
                key_width + 20,
                40,
            ),
        ]

        for key, value in attributes.items():

            display_name = display_names[key]

            lines.append(
                f"{display_name:<{key_width}} : {value}"
            )

        return "\n".join(lines)

    def print(self) -> None:
        """Print the R3XA file in a compact human-readable format."""

        print(
            self._format_attributes()
        )

    def __str__(self) -> str:
        """Return a human-readable representation."""

        return self._format_attributes()

    def __repr__(self) -> str:
        """Return a human-readable representation."""

        return self._format_attributes()
