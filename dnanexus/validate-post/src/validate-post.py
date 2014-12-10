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

import sys, os, subprocess, json, requests, shlex, urlparse, logging
import dxpy

print sys.path
print subprocess.check_output(['ls','-l'])

from dxencode import dxencode as dxencode

logger = logging.getLogger("Applet")

'''
        {
            "dataset": "ENCSR000ACY",
            "file_format": "fastq",
            "file_size": os.path.getsize(path),
            "md5sum": md5sum.hexdigest(),
            "output_type": "raw data",
            "submitted_file_name": path,
            "lab": my_lab,
            "award": my_award
        }
'''
root_dir = os.environ.get('DX_FS_ROOT') or ""
DATA = root_dir+"/opt/data/"
encValData  = DATA+'encValData'
validate_map = {
    'bam': ['-type=bam'],
    'bed': ['-type=bed6+'],  # if this fails we will drop to bed3+
    'bedLogR': ['-type=bigBed9+1', '-as=%s/as/bedLogR.as' % encValData],
    'bed_bedLogR': ['-type=bed9+1', '-as=%s/as/bedLogR.as' % encValData],
    'bedMethyl': ['-type=bigBed9+2', '-as=%s/as/bedMethyl.as' % encValData],
    'bed_bedMethyl': ['-type=bed9+2', '-as=%s/as/bedMethyl.as' % encValData],
    'bigBed': ['-type=bigBed6+'],  # if this fails we will drop to bigBed3+
    'bigWig': ['-type=bigWig'],
    'broadPeak': ['-type=bigBed6+3', '-as=%s/as/broadPeak.as' % encValData],
    'bed_broadPeak': ['-type=bed6+3', '-as=%s/as/broadPeak.as' % encValData],
    'fasta': ['-type=fasta'],
    'fastq': ['-type=fastq'],
    'gtf': None,
    'idat': ['-type=idat'],
    'narrowPeak': ['-type=bigBed6+4', '-as=%s/as/narrowPeak.as' % encValData],
    'bed_narrowPeak': ['-type=bed6+4', '-as=%s/as/narrowPeak.as' % encValData],
    'rcc': ['-type=rcc'],
    'tar': None,
    'tsv': None,
    '2bit': None,
    'csfasta': ['-type=csfasta'],
    'csqual': ['-type=csqual'],
    'bedRnaElements': ['-type=bed6+3', '-as=%s/as/bedRnaElements.as' % encValData],
    'CEL': None,
}

def validate(filename, file_meta):
    # Change the following to process whatever input this stage
    # receives.  You may also want to copy and paste the logic to download
    # and upload files here as well if this stage receives file input
    # and/or makes file output.

    logger.debug(file_meta)

    logger.debug("Run Validate Files on %s" % filename)
    validate_args = validate_map.get(file_meta['file_format'])
    assembly = file_meta.get('assembly')
    if assembly:
        chromInfo = ['-chromInfo=%s/%s/chrom.sizes' % (encValData, assembly)]
    else:
        chromInfo = ['-chromInfo=%s/hg19/chrom.sizes' % encValData]

    print subprocess.check_output(['ls','-l'])
    valid = "Not validated yet"
    if validate_args is not None:
        logger.debug(("Validating file."))
        validation_command = ['validateFiles'] + validate_args + chromInfo + ['-doReport'] + [filename]
        try:
            logger.debug( " ".join(validation_command) )
            valid = subprocess.check_output(validation_command)
        except subprocess.CalledProcessError as e:
            pass
            logger.debug((e.output))

    else:
        return {
            "report": None,
            "validation": "Not Run for type: " % file_meta['file_format']
        }

    logger.debug(valid)
    print subprocess.check_output(['ls','-l'])
    logger.debug("Upload result")
    report_dxfile = dxpy.upload_local_file("%s.report" % filename)
    logger.debug(report_dxfile)
    ## is_valid == 'Error count 0'
    return {
        "report": report_dxfile,
        "validation": valid
    }

@dxpy.entry_point("main")
def main(pipe_file, file_meta, key=None, debug=False):

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

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    (AUTHID,AUTHPW,SERVER) = dxencode.processkey(key)

    filename = dxpy.describe(pipe_file)['name']
    dx_file = dxpy.download_dxfile(pipe_file, filename)

    file_meta['path'] = filename
    file_meta['md5sum'] = dxencode.calc_md5(filename).hexdigest()
    file_meta['file_size'] = os.path.getsize(filename)

    v = validate(filename, file_meta)
    if v['validation'] == "Error count 0\n":   ## yes with CR

        print("Submitting metadata.")
        f_obj = dxencode.encoded_post_file(file_meta, SERVER, AUTHID, AUTHPW)
        logger.info(json.dumps(f_obj, indent=4, sort_keys=True))

    else:
        print "File invalid: %s" % v['validation']


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


    return v

dxpy.run()
