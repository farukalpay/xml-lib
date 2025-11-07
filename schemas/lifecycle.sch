<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron"
        queryBinding="xslt2">

  <title>XML Lifecycle Validation Rules</title>

  <ns prefix="xsl" uri="http://www.w3.org/1999/XSL/Transform"/>

  <!-- Cross-file ID uniqueness -->
  <pattern id="unique-ids">
    <rule context="*[@id]">
      <let name="id" value="@id"/>
      <assert test="count(//*[@id = $id]) = 1">
        ID '<value-of select="$id"/>' must be unique across all documents
      </assert>
    </rule>
  </pattern>

  <!-- Temporal monotonicity: timestamps must increase through lifecycle -->
  <pattern id="temporal-order">
    <rule context="document">
      <let name="begin-time" value="phases/phase[@name='begin']/@timestamp"/>
      <let name="start-time" value="phases/phase[@name='start']/@timestamp"/>
      <let name="iteration-time" value="phases/phase[@name='iteration']/@timestamp"/>
      <let name="end-time" value="phases/phase[@name='end']/@timestamp"/>
      <let name="continuum-time" value="phases/phase[@name='continuum']/@timestamp"/>

      <assert test="not($begin-time and $start-time) or $begin-time &lt;= $start-time">
        Begin timestamp must precede or equal Start timestamp
      </assert>
      <assert test="not($start-time and $iteration-time) or $start-time &lt;= $iteration-time">
        Start timestamp must precede or equal Iteration timestamp
      </assert>
      <assert test="not($iteration-time and $end-time) or $iteration-time &lt;= $end-time">
        Iteration timestamp must precede or equal End timestamp
      </assert>
      <assert test="not($end-time and $continuum-time) or $end-time &lt;= $continuum-time">
        End timestamp must precede or equal Continuum timestamp
      </assert>
    </rule>
  </pattern>

  <!-- Phase ordering: lifecycle phases must appear in canonical order -->
  <pattern id="phase-order">
    <rule context="phases">
      <let name="phase-names" value="phase/@name"/>
      <let name="begin-pos" value="index-of($phase-names, 'begin')"/>
      <let name="start-pos" value="index-of($phase-names, 'start')"/>
      <let name="iteration-pos" value="index-of($phase-names, 'iteration')"/>
      <let name="end-pos" value="index-of($phase-names, 'end')"/>
      <let name="continuum-pos" value="index-of($phase-names, 'continuum')"/>

      <assert test="not($begin-pos and $start-pos) or $begin-pos[1] &lt; $start-pos[1]">
        Phase 'begin' must appear before 'start'
      </assert>
      <assert test="not($start-pos and $iteration-pos) or $start-pos[1] &lt; $iteration-pos[1]">
        Phase 'start' must appear before 'iteration'
      </assert>
      <assert test="not($iteration-pos and $end-pos) or $iteration-pos[last()] &lt; $end-pos[1]">
        Phase 'iteration' must appear before 'end'
      </assert>
      <assert test="not($end-pos and $continuum-pos) or $end-pos[1] &lt; $continuum-pos[1]">
        Phase 'end' must appear before 'continuum'
      </assert>
    </rule>
  </pattern>

  <!-- Reference integrity: refs must point to existing IDs -->
  <pattern id="reference-integrity">
    <rule context="*[@ref-begin]">
      <let name="ref" value="@ref-begin"/>
      <assert test="//begin[@id = $ref] or //phase[@name='begin'][@id = $ref]">
        Reference '<value-of select="$ref"/>' must point to an existing begin phase
      </assert>
    </rule>

    <rule context="*[@ref-start]">
      <let name="ref" value="@ref-start"/>
      <assert test="//start[@id = $ref] or //phase[@name='start'][@id = $ref]">
        Reference '<value-of select="$ref"/>' must point to an existing start phase
      </assert>
    </rule>

    <rule context="*[@ref-iteration]">
      <let name="ref" value="@ref-iteration"/>
      <assert test="//iteration[@id = $ref] or //phase[@name='iteration'][@id = $ref]">
        Reference '<value-of select="$ref"/>' must point to an existing iteration phase
      </assert>
    </rule>

    <rule context="*[@ref-end]">
      <let name="ref" value="@ref-end"/>
      <assert test="//end[@id = $ref] or //phase[@name='end'][@id = $ref]">
        Reference '<value-of select="$ref"/>' must point to an existing end phase
      </assert>
    </rule>
  </pattern>

  <!-- Checksum validation: if present, must be valid format -->
  <pattern id="checksum-format">
    <rule context="*[@checksum]">
      <assert test="matches(@checksum, '^[a-f0-9]{64}$')">
        Checksum must be a valid SHA-256 hash (64 hex characters)
      </assert>
    </rule>
  </pattern>

  <!-- Iteration cycles must be sequential -->
  <pattern id="iteration-cycles">
    <rule context="iteration[@cycle]">
      <let name="cycle" value="@cycle"/>
      <assert test="$cycle >= 1">
        Iteration cycle must be >= 1
      </assert>
    </rule>
  </pattern>

  <!-- Document must have at least begin phase -->
  <pattern id="minimum-phases">
    <rule context="document/phases">
      <assert test="phase[@name='begin']">
        Document must contain at least a 'begin' phase
      </assert>
    </rule>
  </pattern>

  <!-- Path references must exist (warning) -->
  <pattern id="path-references">
    <rule context="phase/use[@path]">
      <report test="true()" role="warning">
        Path reference: <value-of select="@path"/> (verify file exists)
      </report>
    </rule>
    <rule context="reference[@path]">
      <report test="true()" role="warning">
        Path reference: <value-of select="@path"/> (verify file exists)
      </report>
    </rule>
  </pattern>

</schema>
