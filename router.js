const fs = require('fs')
const express = require('express')
const Paper = require('./mongoose')
const formidable = require('formidable')
const path = require('path')

//创建路由容器
let router = express.Router()

router.get('/api/paper', async function (req, res) {
  let data = await Paper.find({}, { _id: 0, __v: 0 })
  res.send(data)
})
router.get('/api/paper/classify', async function (req, res) {
  let param = req.query.classify
  data = await Paper.aggregate([
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
  let page = req.query.page ? parseInt(req.query.page) : 1
  let size = req.query.size ? parseInt(req.query.size) : 10
  let startDate = req.query.date ? req.query.date[0] : '1900-00-00'
  let endDate = req.query.date ? req.query.date[1] : '2100-00-00'
  let params = [{ date: { $gte: startDate, $lte: endDate } }]
  req.query.pubs ? params.push({ publication: { $in: req.query.pubs } }) : params
  req.query.area ? params.push({ areas: req.query.area }) : params
  if (req.query.text) {
    let reg = new RegExp(req.query.text, 'i')
    let selector = { $or: [{ title: { $regex: reg } }, { abstract: { $regex: reg } }, { DOI: { $regex: reg } }, { authors: { $regex: reg } }] }
    params.push(selector)
  }
  data = await Paper.aggregate([
    {
      $match: { $and: params }
    },
    { $sort: { date: -1, _id: 1 } },
    {
      $facet: {
        total: [{ $count: 'total' }],
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
  console.log('收到', data.DOI)
  try {
    if (await Paper.findOne({ DOI: data.DOI })) {
      res.status(500).send('数据已存在')
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
//   let data = await Paper.find({}, { _id: 0, __v: 0 })
//   data.forEach(async item => {
//     let date = item.date.split(' ')[0]
//     let pub = ''
//     if (item.publication == 'PhysRevB') {
//       pub = 'Physical Review B'
//     } else if (item.publication == 'PhysRevA') {
//       pub = 'Physical Review A'
//     } else if (item.publication == 'PhysRevLett') {
//       pub = 'Physical Review Letters'
//     } else if (item.publication == 'PhysRevResearch') {
//       pub = 'Physical Review Research'
//     } else if (item.publication == 'RevModPhys') {
//       pub = 'Reviews of Modern Physics'
//     } else {
//       console.log('No found')
//     }
//     await Paper.findOneAndUpdate({ DOI: item.DOI }, { $set: { publication: pub, date: date } })
//     console.log('OK' + item.DOI)
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
      let cmdStr = 'C:/ProgramData/Anaconda3/envs/spider/python.exe d:/database/web/node/RPDB_Server/pdfscanner.py'
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
            throw err
          }
          let sucDate = new Date()
          console.log('文件已删除！时间：' + sucDate)
        })
      })
    }
  })
})

module.exports = router
