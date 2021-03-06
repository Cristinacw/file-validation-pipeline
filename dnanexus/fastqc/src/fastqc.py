#!/usr/bin/env python
# fastqc 0.0.1
# Generated by dx-app-wizard.
#
# Parallelized execution pattern: Your app will generate multiple jobs
# to perform some computation in parallel, followed by a final
# "postprocess" stage that will perform any additional computations as
# necessary.
#
# See https://wiki.dnanexus.com/Developer-Portal for documentation and
# tutorials on how to modify this file.
#
# DNAnexus Python Bindings (dxpy) documentation:
#   http://autodoc.dnanexus.com/bindings/python/current/

import os, subprocess, shlex, time
import dxpy

@dxpy.entry_point("postprocess")
def postprocess(reports):
    # Change the following to process whatever input this stage
    # receives.  You may also want to copy and paste the logic to download
    # and upload files here as well if this stage receives file input
    # and/or makes file output.

    #for output in reports:
    #   pass
    return reports

@dxpy.entry_point("process")
def process(fastq):
    # Change the following to process whatever input this stage
    # receives.  You may also want to copy and paste the logic to download
    # and upload files here as well if this stage receives file input
    # and/or makes file output.

    print fastq
    reads_filename = dxpy.describe(fastq)['name']
    reads_basename = reads_filename.rstrip('.gz').rstrip('.fq').rstrip('.fastq')
    reads_file = dxpy.download_dxfile(fastq,"fastq.gz")

    subprocess.check_call(['mkdir', 'output'])
    print "Run QC"
    fqc_command = "/usr/bin/FastQC/fastqc fastq.gz -o output"
    print fqc_command
    stdio = subprocess.check_output(shlex.split(fqc_command))
    print stdio
    print subprocess.check_output(['ls','-l', 'output'])
    subprocess.check_call(['unzip', 'output/fastq_fastqc.zip'])
    print "Upload results"
    subprocess.check_call(['mv', 'fastq_fastqc/fastqc_data.txt', "%s_data.txt" % reads_basename])
    subprocess.check_call(['mv', 'fastq_fastqc/summary.txt', "%s_summary.txt" % reads_basename])
    subprocess.check_call(['mv','output/fastq_fastqc.zip', "%s_fastqc.zip" % reads_basename])
    report_dxfile = dxpy.upload_local_file("%s_data.txt" % reads_basename)
    summary_dxfile = dxpy.upload_local_file("%s_summary.txt" % reads_basename)
    zip_dxfile = dxpy.upload_local_file("%s_fastqc.zip" % reads_basename)
    print report_dxfile
    return {
        "report": report_dxfile,
        "summary": summary_dxfile,
        "zip": zip_dxfile
    }

@dxpy.entry_point("main")
def main(files):

    # The following line(s) initialize your data object inputs on the platform
    # into dxpy.DXDataObject instances that you can start using immediately.

    #files = [dxpy.DXFile(item) for item in files]

    # The following line(s) download your file inputs to the local file system
    # using variable names for the filenames.

    #for i, f in enumerate(files):
    #    dxpy.download_dxfile(f.get_id(), "files-" + str(i))

    # Split your work into parallel tasks.  As an example, the
    # following generates 10 subjobs running with the same dummy
    # input.

    subjobs = []
    for fastq in files:
        subjob_input = { "fastq": fastq }
        subjobs.append(dxpy.new_dxjob(subjob_input, "process"))

    # The following line creates the job that will perform the
    # "postprocess" step of your app.  We've given it an input field
    # that is a list of job-based object references created from the
    # "process" jobs we just created.  Assuming those jobs have an
    # output field called "output", these values will be passed to the
    # "postprocess" job.  Because these values are not ready until the
    # "process" jobs finish, the "postprocess" job WILL NOT RUN until
    # all job-based object references have been resolved (i.e. the
    # jobs they reference have finished running).
    #
    # If you do not plan to have the "process" jobs create output that
    # the "postprocess" job will require, then you can explicitly list
    # the dependencies to wait for those jobs to finish by setting the
    # "depends_on" field to the list of subjobs to wait for (it
    # accepts either dxpy handlers or string IDs in the list).  We've
    # included this parameter in the line below as well for
    # completeness, though it is unnecessary if you are providing
    # job-based object references in the input that refer to the same
    # set of jobs.
    '''
    postprocess_job = dxpy.new_dxjob(fn_input={
                "report": [subjob.get_output_ref("report") for subjob in subjobs],
                "summary": [subjob.get_output_ref("summary") for subjob in subjobs],
                "zips": [subjob.get_output_ref("zips") for subjob in subjobs],
                },
                fn_name="postprocess",
                depends_on=subjobs)
    '''
    # If you would like to include any of the output fields from the
    # postprocess_job as the output of your app, you should return it
    # here using a job-based object reference.  If the output field in
    # the postprocess function is called "answer", you can pass that
    # on here as follows:
    #
    #return { "FastQC_reports": [ dxpy.dxlink(item) for item in postprocess_job.get_output_ref("report") ]}
    #
    # Tip: you can include in your output at this point any open
    # objects (such as gtables) which will be closed by a job that
    # finishes later.  The system will check to make sure that the
    # output object is closed and will attempt to clone it out as
    # output into the parent container only after all subjobs have
    # finished.

    output = {
                "reports": [subjob.get_output_ref("report") for subjob in subjobs],
                "summaries": [subjob.get_output_ref("summary") for subjob in subjobs],
                "zips": [subjob.get_output_ref("zip") for subjob in subjobs],
    }

    '''
    for job in postprocess_job.get_output_ref("reports"):
        item = dxpy.dxlink(job)
        output['FastQC_reports'].append(item['report'])
        output['FastQC_zip'].append(item['zip'])
        output['FastQC_summary'].append(item['summary'])
    '''

#    output["FastQC_reports"] = [ dxpy.dxlink(item)  for item in FastQC_reports]
#    output["FastQC_reports"] = FastQC_reports
#    output["FastQC_zip"] = FastQC_zip
#    output["FastQC_summary"] = FastQC_summary

    return output

dxpy.run()
