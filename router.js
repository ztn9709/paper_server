const fs = require('fs')
const express = require('express')
const Paper = require('./mongoose')
const formidable = require('formidable')
const path = require('path')

//创建路由容器
let router = express.Router()

router.get('/api/paper', async function (req, res) {
  let data = await Paper.find({}, { _id: 0, __v: 0 }).sort({ date: -1, DOI: -1 })
  res.send(data)
})
router.get('/api/paper/classify', async function (req, res) {
  let param = req.query.classify
  data = await Paper.aggregate([
    // { $match: { topo_label: 1 } },
    { $unwind: `$${param}` },
    {
      $group: {
        _id: `$${param}`,
        value: { $sum: 1 }
      }
    },
    {
      $sort: { value: -1 }
    }
  ])
  res.send(data)
})
router.get('/api/paper/search', async function (req, res) {
  let sort = { date: -1, DOI: -1 }
  let page = req.query.page ? parseInt(req.query.page) : 1
  let size = req.query.size ? parseInt(req.query.size) : 10
  let params = []
  req.query.date
    ? params.push({ date: { $gte: req.query.date[0], $lte: req.query.date[1] } })
    : params.push({ date: { $gte: '1900-00-00' } })
  req.query.subs ? params.push({ topo_label: { $in: req.query.subs.map(Number) } }) : params
  req.query.pubs ? params.push({ publication: { $in: req.query.pubs } }) : params
  req.query.areas ? params.push({ areas: { $in: req.query.areas } }) : params
  req.query.DOI ? params.push({ DOI: req.query.DOI }) : params
  if (req.query.text) {
    params.push({ $text: { $search: req.query.text } })
    sort = { score: { $meta: 'textScore' } }
  }
  if (req.query.authors) {
    let text = req.query.authors.replace(/[~`!@#$%^&*()+={}\[\];:\'\"<>.,\/\\-_]/g, '\\$&')
    let reg = new RegExp(text, 'i')
    params.push({ authors: { $regex: reg } })
  }
  sort = req.query.sort ? { date: parseInt(req.query.sort), DOI: parseInt(req.query.sort) } : sort
  data = await Paper.aggregate([
    {
      $match: { $and: params }
    },
    { $sort: sort },
    {
      $facet: {
        total: [{ $count: 'total' }],
        groupSub: [
          {
            $group: {
              _id: '$topo_label',
              value: { $sum: 1 }
            }
          }
        ],
        groupPub: [
          {
            $group: {
              _id: '$publication',
              value: { $sum: 1 }
            }
          }
        ],
        groupArea: [
          { $unwind: '$areas' },
          {
            $group: {
              _id: '$areas',
              value: { $sum: 1 }
            }
          }
        ],
        data: [{ $skip: (page - 1) * size }, { $limit: size }]
      }
    }
  ])
  res.send(data)
})
router.post('/api/paper', async function (req, res) {
  let data = req.body
  data.topo_label = parseInt(data.topo_label)
  console.log('收到', data.DOI)
  try {
    if (await Paper.findOne({ DOI: data.DOI })) {
      res.status(400).send('数据已存在')
      console.log('已存在')
    } else {
      await new Paper(data).save()
      console.log('存储成功')
      res.status(200).send('存储成功')
    }
  } catch (err) {
    res.status(500).send('数据库存储出错:' + err)
    console.log('catch: ', err)
  }
})
// router.get('/api/paper/update', async function (req, res) {
//   let data = await Paper.aggregate([
//     { $group: { _id: '$DOI', value: { $sum: 1 } } },
//     { $match: { value: { $gt: 1 } } }
//   ])
//   console.log(data)
//   data.forEach(async item => {
//     await Paper.findOneAndDelete({ DOI: item._id })
//   })
//   res.send('OK')
// })
router.post('/api/pdf2doi', function (req, res) {
  const form = new formidable.IncomingForm()
  form.uploadDir = path.join(__dirname, 'public', 'pdf_temp')
  form.options.keepExtensions = true
  form.parse(req, (err, fields, files) => {
    if (err) {
      console.error(err)
      res.status(500).send('文件上传错误！')
    } else {
      let cmdStr =
        'C:/ProgramData/Anaconda3/envs/spider/python.exe D:/database/sci_paper_db/server/pdfscanner.py --path ' +
        files.file.filepath
      require('child_process').exec(cmdStr, (err, stdout, stderr) => {
        if (err) {
          console.error(err)
          res.status(400).send('PDF文件解析失败！')
        } else {
          let data = JSON.parse(stdout)
          res.send(data)
          stderr ? console.log('解析不完全，错误信息：', stderr) : console.log('解析成功')
        }
        fs.unlink(files.file.filepath, err => {
          if (err) {
            console.error(err)
          }
          let sucDate = new Date()
          console.log('文件已删除！时间：' + sucDate)
        })
      })
    }
  })
})

module.exports = router
